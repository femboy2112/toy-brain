#!/usr/bin/env python3
"""Stage C.1 dynamic Codex flow orchestrator for Claude Code.

Contract:
- Claude remains orchestrator/integrator.
- Codex executes bounded implementation nodes only through this wrapper.
- The wrapper schedules a dependency DAG with at most two active Codex sessions.
- Each Codex node runs workspace-write inside an isolated temp git worktree.
- Dependency outputs are overlaid only for nodes that explicitly depend on them.
- Final live-repo copy-back happens only after every node succeeds and final
  apply preflight passes.
- Network/retry diagnostics are separated from semantic JSONL output and do not
  count against semantic output caps.
- The wrapper never stages, commits, pushes, restores, rebases, merges, or uses
  shell=True.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Iterable


EXIT_SUCCESS = 0
EXIT_WRAPPER_INTERNAL = 1
EXIT_INVALID_ARGS = 2
EXIT_CODEX_BINARY_MISSING = 10
EXIT_CODEX_AUTH_MISSING_OR_INVALID = 11
EXIT_CODEX_UNSUPPORTED_FLAG = 12
EXIT_CODEX_MODEL_INVALID = 13
EXIT_CODEX_EFFORT_INVALID = 14
EXIT_CODEX_TIMEOUT = 20
EXIT_CODEX_NONZERO_EXIT = 21
EXIT_CODEX_OUTPUT_TOO_LARGE = 22
EXIT_CODEX_RAW_OUTPUT_TOO_LARGE = 23
EXIT_JSON_PARSE_ERROR = 30
EXIT_LIVE_WORKTREE_DIRTY = 31
EXIT_ALLOWED_PATH_INVALID = 32
EXIT_OUT_OF_SCOPE_DIFF = 33
EXIT_APPLY_FAILED = 34
EXIT_WORKTREE_SETUP_FAILED = 35
EXIT_WORKTREE_CLEANUP_FAILED = 36
EXIT_RATE_LIMIT_STATE_ERROR = 37
EXIT_SYMLINK_PATH_REJECTED = 38
EXIT_MANIFEST_INVALID = 40
EXIT_COLLISION_DETECTED = 41
EXIT_PARALLEL_LIMIT_EXCEEDED = 42
EXIT_NODE_FAILED = 43
EXIT_APPLY_PREFLIGHT_FAILED = 44
EXIT_CODEX_NETWORK_TRANSIENT = 45
EXIT_FLOW_BLOCKED = 46
EXIT_CALL_BUDGET_EXCEEDED = 47


EFFORT_VALUES = {"low", "medium", "high"}
EFFORT_TIMEOUT_DEFAULTS = {"low": 180, "medium": 600, "high": 1200}
MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]+$")
DEFAULT_AUDIT_DIR = ".claude/codex_bridge_logs"
DEFAULT_STATE_DIR = ".claude/codex_bridge_state"
DEFAULT_MIN_FLOW_INTERVAL_SECONDS = 180
DEFAULT_MIN_START_GAP_SECONDS = 30
DEFAULT_MAX_PARALLEL = 2
DEFAULT_MAX_TOTAL_CALLS = 3
OPERATOR_APPROVED_MAX_TOTAL_CALLS = 8

AUTH_PATTERNS = (
    "not logged in",
    "logged out",
    "login required",
    "run codex login",
    "sign in",
    "signin",
    "unauthenticated",
    "authentication",
    "no api key",
    "api key required",
    "no access token",
    "access token required",
)

NETWORK_PATTERNS = (
    "network error",
    "networkerror",
    "stream disconnected",
    "connection reset",
    "connection aborted",
    "connection closed",
    "socket hang up",
    "econnreset",
    "etimedout",
    "timed out",
    "timeout",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "http 429",
    "http 500",
    "http 502",
    "http 503",
    "http 504",
    "status 429",
    "status 500",
    "status 502",
    "status 503",
    "status 504",
    "rate limit",
    "too many requests",
    "retry later",
    "temporarily unavailable",
    "websocket",
    "ws error",
    "transport error",
)


class SymlinkPathRejected(Exception):
    pass


@dataclass(frozen=True)
class Node:
    node_id: str
    prompt: str
    allowed_files: tuple[str, ...]
    read_files: tuple[str, ...] = ()
    allow_delete: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    model: str = "gpt-5.5"
    effort: str = "high"
    timeout: int = 1200
    kind: str = "write"


@dataclass
class NetworkSummary:
    line_count: int = 0
    byte_count: int = 0
    sha256: str | None = None
    stdout_noise_lines: int = 0
    stderr_noise_lines: int = 0
    retryable: bool = False


@dataclass
class NodeResult:
    node_id: str
    exit_code: int
    error_class: str | None
    worktree: str
    stdout_semantic: str = ""
    stderr_semantic: str = ""
    codex_returncode: int | None = None
    changed_paths: set[str] = field(default_factory=set)
    out_of_scope_paths: set[str] = field(default_factory=set)
    json_events: int = 0
    agent_messages: list[str] = field(default_factory=list)
    command_count: int = 0
    file_change_count: int = 0
    duration_ms: int = 0
    network: NetworkSummary = field(default_factory=NetworkSummary)


@dataclass
class FlowState:
    task: str
    nodes: list[Node]
    node_by_id: dict[str, Node]
    dependency_closure: dict[str, set[str]]
    completed: dict[str, NodeResult] = field(default_factory=dict)
    failed: NodeResult | None = None
    launched_order: list[str] = field(default_factory=list)
    integrated_paths_by_node: dict[str, set[str]] = field(default_factory=dict)
    max_simultaneous_observed: int = 0
    network_noise_lines: int = 0
    network_noise_bytes: int = 0
    retryable_network_failures: int = 0


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds")


def bounded(value: str, limit: int = 5000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n...[truncated {len(value) - limit} chars]"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded dynamic Codex DAG flow with at most two active Codex nodes.")
    parser.add_argument("--manifest", help="JSON manifest defining one dynamic flow")
    parser.add_argument("--cwd", default=".", help="Live repository root")
    parser.add_argument("--apply", action="store_true", help="Apply successful flow changes back to live repo")
    parser.add_argument("--model", default="gpt-5.5", help="Default model for nodes")
    parser.add_argument("--effort", default="high", help="Default effort for nodes: low, medium, high")
    parser.add_argument("--timeout", type=int, help="Default timeout seconds; defaults by effort")
    parser.add_argument("--max-parallel", type=int, default=DEFAULT_MAX_PARALLEL)
    parser.add_argument("--max-total-calls", type=int, default=DEFAULT_MAX_TOTAL_CALLS)
    parser.add_argument("--operator-approved-over-three-calls", action="store_true")
    parser.add_argument("--min-flow-interval-seconds", type=int, default=DEFAULT_MIN_FLOW_INTERVAL_SECONDS)
    parser.add_argument("--min-start-gap-seconds", type=int, default=DEFAULT_MIN_START_GAP_SECONDS)
    parser.add_argument("--max-prompt-chars", type=int, default=80000)
    parser.add_argument("--max-raw-stdout-chars", type=int, default=1024 * 1024)
    parser.add_argument("--max-raw-stderr-chars", type=int, default=256 * 1024)
    parser.add_argument("--max-semantic-output-chars", type=int, default=64000)
    parser.add_argument("--prompt-template", help="Optional worker template; defaults to prompts/orchestrate_flow_worker.md")
    parser.add_argument("--audit-dir", default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    parser.add_argument("--codex-executable", default="codex")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--selftest-no-pacing", action="store_true")
    return parser.parse_args(argv)


def emit_report(*, status: str, exit_code: int, error_class: str | None, metadata: Mapping[str, Any], text: str = "") -> None:
    wrapper = {"status": status, "exit_code": exit_code, "error_class": error_class, **dict(metadata)}
    print("codex_chatgpt_flow_orchestrator transport report")
    print()
    print("Wrapper metadata:")
    print(json.dumps(wrapper, indent=2, sort_keys=True))
    if text:
        print()
        print("Flow output:")
        print(text, end="" if text.endswith("\n") else "\n")


def fail(*, exit_code: int, error_class: str, message: str, metadata: Mapping[str, Any] | None = None, text: str = "") -> int:
    meta = dict(metadata or {})
    meta["message"] = message
    emit_report(status="error", exit_code=exit_code, error_class=error_class, metadata=meta, text=text)
    return exit_code


def run_small(args: list[str], *, timeout: int = 15, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False, cwd=cwd)


def git(args: list[str], *, cwd: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return run_small(["git", *args], timeout=timeout, cwd=cwd)


def repo_root(cwd: str) -> str:
    proc = git(["rev-parse", "--show-toplevel"], cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"not a git repo: {cwd}; stderr={bounded(proc.stderr)}")
    return proc.stdout.strip()


def git_status_porcelain(cwd: str) -> list[str]:
    proc = git(["status", "--porcelain", "--untracked-files=all"], cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"git status failed: {bounded(proc.stderr)}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def parse_status_paths(lines: list[str]) -> set[str]:
    paths: set[str] = set()
    for line in lines:
        if len(line) < 4:
            continue
        raw = line[3:]
        if " -> " in raw:
            old, new = raw.split(" -> ", 1)
            paths.add(old.strip().strip('"'))
            paths.add(new.strip().strip('"'))
        else:
            paths.add(raw.strip().strip('"'))
    return paths


def resolve_executable(executable: str) -> str | None:
    if os.path.sep in executable or (os.path.altsep and os.path.altsep in executable):
        path = Path(executable)
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(executable)


def validate_model(model: str) -> str:
    if not model:
        raise ValueError("model is required")
    if not MODEL_RE.match(model):
        raise ValueError("model contains unsupported characters; allowed: A-Z a-z 0-9 . _ : / -")
    return model


def validate_effort(effort: str) -> str:
    if effort not in EFFORT_VALUES:
        raise ValueError(f"effort must be one of {sorted(EFFORT_VALUES)}")
    return effort


def validate_path(path_text: str, *, repo: str, label: str) -> str:
    if not path_text:
        raise ValueError(f"empty {label} path")
    p = Path(path_text)
    if p.is_absolute():
        raise ValueError(f"absolute paths are not allowed for {label}: {path_text}")
    if any(part == ".." for part in p.parts):
        raise ValueError(f"parent traversal is not allowed for {label}: {path_text}")
    if p.parts and p.parts[0] == ".git":
        raise ValueError(f".git paths are not allowed for {label}: {path_text}")
    normalized = str(p.as_posix())
    if normalized in {".", ""}:
        raise ValueError(f"invalid {label} path: {path_text}")
    live_path = Path(repo) / normalized
    if live_path.is_symlink():
        raise SymlinkPathRejected(f"symlinks are not allowed for {label}: {path_text}")
    if live_path.exists() and live_path.is_dir():
        raise ValueError(f"directories are not allowed as exact file paths for {label}: {path_text}")
    return normalized


def probe_codex(codex_path: str) -> dict[str, Any]:
    version_proc = run_small([codex_path, "--version"], timeout=10)
    version_text = (version_proc.stdout or version_proc.stderr).strip()
    help_proc = run_small([codex_path, "exec", "--help"], timeout=15)
    help_text = (help_proc.stdout or "") + "\n" + (help_proc.stderr or "")
    if help_proc.returncode != 0:
        return {"codex_version": version_text, "supported": False, "unsupported": ["exec_help"], "capabilities": {}, "exec_help_excerpt": bounded(help_text)}
    capabilities = {
        "config_override": ("-c" in help_text and ("--config" in help_text or "config" in help_text.lower())),
        "sandbox": "--sandbox" in help_text,
        "workspace_write": "workspace-write" in help_text,
        "ephemeral": "--ephemeral" in help_text,
        "skip_git_repo_check": "--skip-git-repo-check" in help_text,
        "model": ("--model" in help_text or "-m" in help_text),
        "cd_flag": ("--cd" in help_text or " -C" in help_text or "-C," in help_text),
        "json": "--json" in help_text,
    }
    required = ["config_override", "sandbox", "workspace_write", "ephemeral", "skip_git_repo_check", "model", "cd_flag", "json"]
    unsupported = [name for name in required if not capabilities.get(name)]
    return {"codex_version": version_text, "supported": not unsupported, "unsupported": unsupported, "capabilities": capabilities}


def auth_status(codex_path: str) -> dict[str, Any]:
    try:
        proc = run_small([codex_path, "login", "status"], timeout=15)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"auth_status": "unknown", "auth_detail": f"login status probe failed: {type(exc).__name__}"}
    text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    low = text.lower()
    if proc.returncode == 0:
        return {"auth_status": "ok", "auth_detail": bounded(text, 500)}
    if any(pat in low for pat in AUTH_PATTERNS):
        return {"auth_status": "missing_or_invalid", "auth_detail": bounded(text, 500)}
    return {"auth_status": "unknown", "auth_detail": bounded(text, 500)}


def default_template_path() -> Path:
    return Path(__file__).resolve().parent / "prompts" / "orchestrate_flow_worker.md"


def load_template(args: argparse.Namespace) -> tuple[str, Path]:
    template_path = Path(args.prompt_template) if args.prompt_template else default_template_path()
    return template_path.read_text(encoding="utf-8"), template_path


def read_manifest(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def topological_closure(node_by_id: dict[str, Node]) -> dict[str, set[str]]:
    visiting: set[str] = set()
    visited: set[str] = set()
    closure: dict[str, set[str]] = {}

    def dfs(node_id: str) -> set[str]:
        if node_id in closure:
            return set(closure[node_id])
        if node_id in visiting:
            raise ValueError(f"dependency cycle detected at node {node_id}")
        visiting.add(node_id)
        deps_total: set[str] = set()
        node = node_by_id[node_id]
        for dep in node.depends_on:
            if dep not in node_by_id:
                raise ValueError(f"node {node_id} depends on unknown node {dep}")
            deps_total.add(dep)
            deps_total.update(dfs(dep))
        visiting.remove(node_id)
        visited.add(node_id)
        closure[node_id] = set(deps_total)
        return deps_total

    for node_id in node_by_id:
        dfs(node_id)
    return closure


def normalize_manifest(
    manifest: dict[str, Any],
    *,
    repo: str,
    default_model: str,
    default_effort: str,
    default_timeout: int,
) -> tuple[str, list[Node], dict[str, Node], dict[str, set[str]]]:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    task = manifest.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("manifest.task must be a non-empty string")

    defaults = manifest.get("defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise ValueError("manifest.defaults must be an object if present")

    nodes_raw = manifest.get("nodes")
    if not isinstance(nodes_raw, list) or not nodes_raw:
        raise ValueError("manifest.nodes must be a non-empty array")

    nodes: list[Node] = []
    seen: set[str] = set()
    for idx, raw in enumerate(nodes_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"node {idx} must be an object")
        node_id = raw.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError(f"node {idx} requires non-empty id")
        if node_id in seen:
            raise ValueError(f"duplicate node id: {node_id}")
        seen.add(node_id)

        prompt = raw.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"node {node_id} requires non-empty prompt")

        allowed_raw = raw.get("allowed_files")
        if not isinstance(allowed_raw, list) or not allowed_raw:
            raise ValueError(f"node {node_id} requires non-empty allowed_files list")

        read_raw = raw.get("read_files", [])
        delete_raw = raw.get("allow_delete", [])
        deps_raw = raw.get("depends_on", [])
        if not isinstance(read_raw, list) or not isinstance(delete_raw, list) or not isinstance(deps_raw, list):
            raise ValueError(f"node {node_id}: read_files/allow_delete/depends_on must be arrays")

        allowed = tuple(validate_path(str(p), repo=repo, label=f"allowed file for {node_id}") for p in allowed_raw)
        reads = tuple(validate_path(str(p), repo=repo, label=f"read file for {node_id}") for p in read_raw)
        deletes = tuple(validate_path(str(p), repo=repo, label=f"allow-delete file for {node_id}") for p in delete_raw)
        if not set(deletes).issubset(set(allowed)):
            raise ValueError(f"node {node_id}: allow_delete paths must also be allowed_files")

        deps = tuple(str(d) for d in deps_raw)
        model = validate_model(str(raw.get("model", defaults.get("model", default_model))))
        effort = validate_effort(str(raw.get("effort", defaults.get("effort", default_effort))))
        timeout = int(raw.get("timeout", defaults.get("timeout", default_timeout)))
        if timeout <= 0:
            raise ValueError(f"node {node_id}: timeout must be positive")
        kind = str(raw.get("kind", "write"))
        if kind != "write":
            raise ValueError(f"node {node_id}: only kind='write' is supported in Stage C.1")

        nodes.append(Node(
            node_id=node_id,
            prompt=prompt,
            allowed_files=allowed,
            read_files=reads,
            allow_delete=deletes,
            depends_on=deps,
            model=model,
            effort=effort,
            timeout=timeout,
            kind=kind,
        ))

    node_by_id = {n.node_id: n for n in nodes}
    closure = topological_closure(node_by_id)
    validate_global_path_relations(nodes, closure)
    return task, nodes, node_by_id, closure


def validate_global_path_relations(nodes: list[Node], closure: dict[str, set[str]]) -> None:
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            a_writes = set(a.allowed_files)
            b_writes = set(b.allowed_files)
            write_overlap = a_writes.intersection(b_writes)
            a_dep_b = b.node_id in closure[a.node_id]
            b_dep_a = a.node_id in closure[b.node_id]
            if write_overlap and not (a_dep_b or b_dep_a):
                raise RuntimeError(
                    f"write/write conflict without dependency between {a.node_id} and {b.node_id}: {sorted(write_overlap)}"
                )


def active_collision(candidate: Node, active_nodes: Iterable[Node]) -> str | None:
    cand_writes = set(candidate.allowed_files)
    cand_reads = set(candidate.read_files)
    for active in active_nodes:
        active_writes = set(active.allowed_files)
        active_reads = set(active.read_files)
        ww = cand_writes.intersection(active_writes)
        if ww:
            return f"write/write active collision with {active.node_id}: {sorted(ww)}"
        rw1 = cand_reads.intersection(active_writes)
        if rw1:
            return f"candidate read/active write collision with {active.node_id}: {sorted(rw1)}"
        rw2 = cand_writes.intersection(active_reads)
        if rw2:
            return f"candidate write/active read collision with {active.node_id}: {sorted(rw2)}"
    return None


def validate_caps(*, nodes: list[Node], max_parallel: int, max_total_calls: int, operator_approved: bool) -> None:
    if max_parallel > 2:
        raise ValueError("max_parallel above 2 is not allowed in Stage C.1")
    if max_parallel < 1:
        raise ValueError("max_parallel must be at least 1")
    if max_total_calls < 1:
        raise ValueError("max_total_calls must be at least 1")
    if max_total_calls > 3 and not operator_approved:
        raise RuntimeError("more than three total Codex calls requires --operator-approved-over-three-calls")
    if len(nodes) > 3 and not operator_approved:
        raise RuntimeError("manifest has more than three Codex nodes; explicit operator approval is required")
    if max_total_calls > OPERATOR_APPROVED_MAX_TOTAL_CALLS:
        raise RuntimeError(f"max_total_calls above {OPERATOR_APPROVED_MAX_TOTAL_CALLS} is not supported by this wrapper")
    if len(nodes) > max_total_calls:
        raise RuntimeError(f"manifest has {len(nodes)} nodes but max_total_calls={max_total_calls}")


def build_prompt(template: str, *, task: str, node: Node, max_prompt_chars: int) -> str:
    allowed_block = "\n".join(f"- {p}" for p in node.allowed_files)
    read_block = "\n".join(f"- {p}" for p in node.read_files) if node.read_files else "- <not declared>"
    delete_block = "\n".join(f"- {p}" for p in node.allow_delete) if node.allow_delete else "- <none>"
    deps_block = "\n".join(f"- {p}" for p in node.depends_on) if node.depends_on else "- <none>"
    prompt = (
        template.rstrip()
        + "\n\n---\n\n# Flow task\n\n"
        + task.strip()
        + "\n\n# Node id\n\n"
        + node.node_id
        + "\n\n# Exact allowed files\n\n"
        + allowed_block
        + "\n\n# Declared read files\n\n"
        + read_block
        + "\n\n# Explicit dependencies\n\n"
        + deps_block
        + "\n\n# Exact allowed deletions\n\n"
        + delete_block
        + "\n\n# Node prompt\n\n"
        + node.prompt.strip()
        + "\n"
    )
    if len(prompt) > max_prompt_chars:
        raise OverflowError(f"node {node.node_id} prompt length {len(prompt)} exceeds {max_prompt_chars}")
    return prompt


def audit_record_path(audit_dir: str) -> Path:
    date = _dt.datetime.now(tz=_dt.timezone.utc).date().isoformat()
    return Path(audit_dir) / f"{date}.jsonl"


def write_audit(audit_dir: str, record: Mapping[str, Any]) -> None:
    path = audit_record_path(audit_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)


class CallLock:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.lock_path = state_dir / "flow_orchestrator_inflight.lock"
        self.fd: int | None = None

    def acquire(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.fd, f"pid={os.getpid()} time={utc_now_iso()}\n".encode("utf-8"))
        except FileExistsError as exc:
            raise RuntimeError(f"another Codex dynamic flow is already in flight: {self.lock_path}") from exc

    def release(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def enforce_flow_interval(state_dir: Path, min_interval: int, *, disabled: bool) -> int:
    if disabled or min_interval <= 0:
        return 0
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "last_flow_orchestrator_run.json"
    waited = 0
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            last = float(data.get("monotonic", 0.0))
        except (OSError, ValueError, TypeError):
            last = 0.0
        elapsed = time.monotonic() - last
        if elapsed < min_interval:
            wait_for = int(min_interval - elapsed) + 1
            time.sleep(wait_for)
            waited = wait_for
    return waited


def record_flow_start(state_dir: Path, *, disabled: bool, node_ids: list[str]) -> None:
    if disabled:
        return
    state_dir.mkdir(parents=True, exist_ok=True)
    data = {"timestamp_utc": utc_now_iso(), "monotonic": time.monotonic(), "pid": os.getpid(), "node_ids": node_ids}
    (state_dir / "last_flow_orchestrator_run.json").write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def setup_worktree(repo: str, label: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", label)
    temp_root = tempfile.mkdtemp(prefix=f"codex-flow-{safe_id}-")
    worktree = str(Path(temp_root) / "repo")
    proc = git(["worktree", "add", "--detach", worktree, "HEAD"], cwd=repo, timeout=120)
    if proc.returncode != 0:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise RuntimeError(f"git worktree add failed for {label}: {bounded(proc.stderr)}")
    return worktree


def cleanup_worktree(repo: str, worktree: str) -> None:
    if not worktree:
        return
    proc = git(["worktree", "remove", "--force", worktree], cwd=repo, timeout=120)
    parent = Path(worktree).parent
    shutil.rmtree(parent, ignore_errors=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git worktree remove failed: {bounded(proc.stderr)}")


def build_codex_argv(codex_path: str, *, node: Node, worktree: str) -> list[str]:
    return [
        codex_path,
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "--ephemeral",
        "--skip-git-repo-check",
        "--cd",
        worktree,
        "-m",
        node.model,
        "-c",
        f"model_reasoning_effort={node.effort}",
        "-",
    ]


def is_network_noise_line(line: str) -> bool:
    low = line.strip().lower()
    if not low:
        return False
    return any(pat in low for pat in NETWORK_PATTERNS)


def split_transport_output(stdout: str, stderr: str, *, max_raw_stdout_chars: int, max_raw_stderr_chars: int) -> tuple[list[str], str, NetworkSummary, str | None]:
    if len(stdout) > max_raw_stdout_chars:
        return [], "", NetworkSummary(), "stdout"
    if len(stderr) > max_raw_stderr_chars:
        return [], "", NetworkSummary(), "stderr"

    semantic_stdout_lines: list[str] = []
    semantic_stderr_lines: list[str] = []
    noise_chunks: list[str] = []
    summary = NetworkSummary()

    for line in stdout.splitlines():
        if is_network_noise_line(line):
            summary.line_count += 1
            summary.stdout_noise_lines += 1
            chunk = line + "\n"
            summary.byte_count += len(chunk.encode("utf-8", errors="replace"))
            noise_chunks.append("stdout:" + chunk)
        else:
            semantic_stdout_lines.append(line)

    for line in stderr.splitlines():
        if is_network_noise_line(line):
            summary.line_count += 1
            summary.stderr_noise_lines += 1
            chunk = line + "\n"
            summary.byte_count += len(chunk.encode("utf-8", errors="replace"))
            noise_chunks.append("stderr:" + chunk)
        else:
            semantic_stderr_lines.append(line)

    if noise_chunks:
        summary.sha256 = sha256_text("".join(noise_chunks))
        summary.retryable = True
    return semantic_stdout_lines, "\n".join(semantic_stderr_lines), summary, None


def parse_json_events(lines: list[str]) -> tuple[int, list[str], int, int]:
    events = 0
    agent_messages: list[str] = []
    command_count = 0
    file_change_count = 0
    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid Codex JSONL at semantic line {lineno}: {exc}") from exc
        events += 1
        item = event.get("item") if isinstance(event, dict) else None
        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    agent_messages.append(text)
            elif item_type == "command_execution":
                command_count += 1
            elif item_type in {"file_change", "file_update"}:
                file_change_count += 1
        if isinstance(event, dict) and event.get("type") == "item.completed":
            item2 = event.get("item")
            if isinstance(item2, dict) and item2.get("type") == "agent_message" and isinstance(item2.get("text"), str):
                if item2["text"] not in agent_messages:
                    agent_messages.append(item2["text"])
    return events, agent_messages, command_count, file_change_count


def snapshot_worktree(root: str) -> dict[str, tuple[str, str]]:
    base = Path(root)
    snap: dict[str, tuple[str, str]] = {}
    for path in base.rglob("*"):
        rel = path.relative_to(base).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        if path.is_dir():
            continue
        if path.is_symlink():
            try:
                snap[rel] = ("symlink", os.readlink(path))
            except OSError:
                snap[rel] = ("symlink", "<unreadable>")
        elif path.is_file():
            snap[rel] = ("file", sha256_bytes(path.read_bytes()))
    return snap


def diff_snapshot(before: dict[str, tuple[str, str]], after: dict[str, tuple[str, str]]) -> set[str]:
    changed: set[str] = set()
    for path in set(before) | set(after):
        if before.get(path) != after.get(path):
            changed.add(path)
    return changed


def copy_path_state(*, src_root: str, dst_root: str, path: str) -> None:
    src = Path(src_root) / path
    dst = Path(dst_root) / path
    if src.is_symlink():
        raise SymlinkPathRejected(f"refusing to copy symlink source: {path}")
    if dst.is_symlink():
        raise SymlinkPathRejected(f"refusing to overwrite symlink destination: {path}")
    if src.exists():
        if src.is_dir():
            raise RuntimeError(f"refusing to copy directory as file path: {path}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    else:
        if dst.exists() or dst.is_symlink():
            if dst.is_dir():
                raise RuntimeError(f"refusing to delete directory as file path: {path}")
            dst.unlink()


def overlay_dependency_outputs(*, integration_worktree: str, node_worktree: str, dep_node_ids: set[str], integrated_paths_by_node: Mapping[str, set[str]]) -> set[str]:
    paths: set[str] = set()
    for dep_id in dep_node_ids:
        paths.update(integrated_paths_by_node.get(dep_id, set()))
    for path in sorted(paths):
        copy_path_state(src_root=integration_worktree, dst_root=node_worktree, path=path)
    return paths


def run_node(
    *,
    repo: str,
    codex_path: str,
    task: str,
    node: Node,
    template: str,
    max_prompt_chars: int,
    max_raw_stdout_chars: int,
    max_raw_stderr_chars: int,
    max_semantic_output_chars: int,
    integration_worktree: str,
    dep_node_ids: set[str],
    integrated_paths_by_node: Mapping[str, set[str]],
) -> NodeResult:
    start = time.monotonic()
    worktree = ""
    try:
        prompt = build_prompt(template, task=task, node=node, max_prompt_chars=max_prompt_chars)
        worktree = setup_worktree(repo, node.node_id)
        overlay_dependency_outputs(
            integration_worktree=integration_worktree,
            node_worktree=worktree,
            dep_node_ids=dep_node_ids,
            integrated_paths_by_node=integrated_paths_by_node,
        )
        before = snapshot_worktree(worktree)
        argv = build_codex_argv(codex_path, node=node, worktree=worktree)
        try:
            completed = subprocess.run(argv, input=prompt, capture_output=True, text=True, timeout=node.timeout, check=False, cwd=worktree)
            raw_stdout = completed.stdout or ""
            raw_stderr = completed.stderr or ""
            codex_returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            return NodeResult(node_id=node.node_id, exit_code=EXIT_CODEX_TIMEOUT, error_class="CODEX_TIMEOUT", worktree=worktree, stderr_semantic=str(exc), duration_ms=int((time.monotonic() - start) * 1000))

        semantic_lines, semantic_stderr, network, raw_too_large = split_transport_output(
            raw_stdout,
            raw_stderr,
            max_raw_stdout_chars=max_raw_stdout_chars,
            max_raw_stderr_chars=max_raw_stderr_chars,
        )
        if raw_too_large:
            return NodeResult(node_id=node.node_id, exit_code=EXIT_CODEX_RAW_OUTPUT_TOO_LARGE, error_class="CODEX_RAW_OUTPUT_TOO_LARGE", worktree=worktree, stderr_semantic=f"{raw_too_large} exceeded raw output safety cap", codex_returncode=codex_returncode, duration_ms=int((time.monotonic() - start) * 1000))

        semantic_stdout = "\n".join(semantic_lines)
        semantic_chars = len(semantic_stdout) + len(semantic_stderr)
        if semantic_chars > max_semantic_output_chars:
            return NodeResult(node_id=node.node_id, exit_code=EXIT_CODEX_OUTPUT_TOO_LARGE, error_class="CODEX_OUTPUT_TOO_LARGE", worktree=worktree, stdout_semantic=bounded(semantic_stdout, 2000), stderr_semantic=bounded(semantic_stderr, 2000), codex_returncode=codex_returncode, network=network, duration_ms=int((time.monotonic() - start) * 1000))

        if codex_returncode != 0:
            combined_semantic = (semantic_stderr + "\n" + semantic_stdout).strip()
            low = combined_semantic.lower()
            if network.retryable or any(pat in (raw_stdout + "\n" + raw_stderr).lower() for pat in NETWORK_PATTERNS):
                return NodeResult(node_id=node.node_id, exit_code=EXIT_CODEX_NETWORK_TRANSIENT, error_class="CODEX_NETWORK_TRANSIENT", worktree=worktree, stdout_semantic=bounded(semantic_stdout, 2000), stderr_semantic=bounded(semantic_stderr, 2000), codex_returncode=codex_returncode, network=network, duration_ms=int((time.monotonic() - start) * 1000))
            err_class = "CODEX_NONZERO_EXIT"
            err_code = EXIT_CODEX_NONZERO_EXIT
            if any(pat in low for pat in AUTH_PATTERNS):
                err_class = "CODEX_AUTH_MISSING_OR_INVALID"
                err_code = EXIT_CODEX_AUTH_MISSING_OR_INVALID
            return NodeResult(node_id=node.node_id, exit_code=err_code, error_class=err_class, worktree=worktree, stdout_semantic=bounded(semantic_stdout, 2000), stderr_semantic=bounded(semantic_stderr, 5000), codex_returncode=codex_returncode, network=network, duration_ms=int((time.monotonic() - start) * 1000))

        try:
            events, agent_messages, command_count, file_change_count = parse_json_events(semantic_lines)
        except ValueError as exc:
            return NodeResult(node_id=node.node_id, exit_code=EXIT_JSON_PARSE_ERROR, error_class="JSON_PARSE_ERROR", worktree=worktree, stdout_semantic=bounded(semantic_stdout, 2000), stderr_semantic=str(exc), codex_returncode=codex_returncode, network=network, duration_ms=int((time.monotonic() - start) * 1000))

        after = snapshot_worktree(worktree)
        changed_paths = diff_snapshot(before, after)
        out_of_scope = changed_paths - set(node.allowed_files)
        if out_of_scope:
            return NodeResult(
                node_id=node.node_id,
                exit_code=EXIT_OUT_OF_SCOPE_DIFF,
                error_class="OUT_OF_SCOPE_DIFF",
                worktree=worktree,
                stdout_semantic=bounded(semantic_stdout, 2000),
                stderr_semantic=semantic_stderr,
                codex_returncode=codex_returncode,
                changed_paths=changed_paths,
                out_of_scope_paths=out_of_scope,
                json_events=events,
                agent_messages=agent_messages,
                command_count=command_count,
                file_change_count=file_change_count,
                network=network,
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        # Reject changed symlinks even if the path is allowed.
        for path in changed_paths:
            p = Path(worktree) / path
            if p.is_symlink():
                return NodeResult(
                    node_id=node.node_id,
                    exit_code=EXIT_SYMLINK_PATH_REJECTED,
                    error_class="SYMLINK_PATH_REJECTED",
                    worktree=worktree,
                    stderr_semantic=f"changed path became symlink: {path}",
                    codex_returncode=codex_returncode,
                    changed_paths=changed_paths,
                    network=network,
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

        return NodeResult(
            node_id=node.node_id,
            exit_code=EXIT_SUCCESS,
            error_class=None,
            worktree=worktree,
            stdout_semantic=semantic_stdout,
            stderr_semantic=semantic_stderr,
            codex_returncode=codex_returncode,
            changed_paths=changed_paths,
            json_events=events,
            agent_messages=agent_messages,
            command_count=command_count,
            file_change_count=file_change_count,
            network=network,
            duration_ms=int((time.monotonic() - start) * 1000),
        )
    except SymlinkPathRejected as exc:
        return NodeResult(node_id=node.node_id, exit_code=EXIT_SYMLINK_PATH_REJECTED, error_class="SYMLINK_PATH_REJECTED", worktree=worktree, stderr_semantic=str(exc), duration_ms=int((time.monotonic() - start) * 1000))
    except RuntimeError as exc:
        return NodeResult(node_id=node.node_id, exit_code=EXIT_WORKTREE_SETUP_FAILED, error_class="WORKTREE_OR_RUNTIME_ERROR", worktree=worktree, stderr_semantic=str(exc), duration_ms=int((time.monotonic() - start) * 1000))


def integrate_node_result(*, integration_worktree: str, result: NodeResult, node: Node) -> None:
    allowed_delete = set(node.allow_delete)
    for path in sorted(result.changed_paths):
        src = Path(result.worktree) / path
        if src.exists():
            copy_path_state(src_root=result.worktree, dst_root=integration_worktree, path=path)
        else:
            if path not in allowed_delete:
                raise RuntimeError(f"Codex deleted {path} in node {node.node_id}, but deletion was not explicitly allowed")
            copy_path_state(src_root=result.worktree, dst_root=integration_worktree, path=path)


def validate_final_apply(*, repo: str, integration_worktree: str, nodes: list[Node]) -> set[str]:
    final_status = git_status_porcelain(integration_worktree)
    changed_paths = parse_status_paths(final_status)
    allowed = set().union(*(set(n.allowed_files) for n in nodes))
    allow_delete = set().union(*(set(n.allow_delete) for n in nodes))
    out = changed_paths - allowed
    if out:
        raise RuntimeError(f"final apply contains out-of-scope paths: {sorted(out)}")
    for path in sorted(changed_paths):
        validate_path(path, repo=repo, label="final apply path")
        src = Path(integration_worktree) / path
        dst = Path(repo) / path
        if src.is_symlink():
            raise SymlinkPathRejected(f"preflight: integration source is a symlink: {path}")
        if dst.is_symlink():
            raise SymlinkPathRejected(f"preflight: live repo destination is a symlink: {path}")
        if src.exists() and src.is_dir():
            raise RuntimeError(f"preflight: integration source is a directory: {path}")
        if not src.exists() and path not in allow_delete:
            raise RuntimeError(f"preflight: integration deleted {path}, but deletion was not explicitly allowed")
    return changed_paths


def apply_final(*, repo: str, integration_worktree: str, changed_paths: set[str]) -> None:
    for path in sorted(changed_paths):
        copy_path_state(src_root=integration_worktree, dst_root=repo, path=path)


def next_ready_node(state: FlowState, *, started: set[str], active_nodes: Iterable[Node]) -> Node | None:
    for node in state.nodes:
        if node.node_id in started or node.node_id in state.completed:
            continue
        if all(dep in state.completed for dep in node.depends_on):
            if active_collision(node, active_nodes) is None:
                return node
    return None


def blocked_ready_reasons(state: FlowState, *, started: set[str], active_nodes: Iterable[Node]) -> list[str]:
    reasons: list[str] = []
    for node in state.nodes:
        if node.node_id in started or node.node_id in state.completed:
            continue
        missing = [dep for dep in node.depends_on if dep not in state.completed]
        if missing:
            reasons.append(f"{node.node_id}: waiting for dependencies {missing}")
            continue
        conflict = active_collision(node, active_nodes)
        if conflict:
            reasons.append(f"{node.node_id}: {conflict}")
    return reasons


def run_flow(
    *,
    repo: str,
    codex_path: str,
    task: str,
    nodes: list[Node],
    node_by_id: dict[str, Node],
    dependency_closure: dict[str, set[str]],
    template: str,
    args: argparse.Namespace,
) -> tuple[int, str | None, FlowState, str, set[str]]:
    state = FlowState(task=task, nodes=nodes, node_by_id=node_by_id, dependency_closure=dependency_closure)
    integration_worktree = setup_worktree(repo, "integration")
    worktrees_to_cleanup: set[str] = {integration_worktree}
    final_changed_paths: set[str] = set()

    started: set[str] = set()
    active: dict[concurrent.futures.Future[NodeResult], Node] = {}
    last_start = 0.0
    error_class: str | None = None
    exit_code = EXIT_SUCCESS

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
            while len(state.completed) < len(nodes):
                # Collect completed node futures.
                for fut in list(active):
                    if not fut.done():
                        continue
                    node = active.pop(fut)
                    result = fut.result()
                    worktrees_to_cleanup.add(result.worktree)
                    state.network_noise_lines += result.network.line_count
                    state.network_noise_bytes += result.network.byte_count
                    if result.exit_code != EXIT_SUCCESS:
                        state.failed = result
                        if result.error_class == "CODEX_NETWORK_TRANSIENT":
                            state.retryable_network_failures += 1
                        error_class = result.error_class or "NODE_FAILED"
                        exit_code = result.exit_code if result.exit_code != EXIT_SUCCESS else EXIT_NODE_FAILED
                        break
                    try:
                        integrate_node_result(integration_worktree=integration_worktree, result=result, node=node)
                    except SymlinkPathRejected:
                        raise
                    except Exception as exc:
                        result.exit_code = EXIT_APPLY_PREFLIGHT_FAILED
                        result.error_class = "INTEGRATION_FAILED"
                        result.stderr_semantic = str(exc)
                        state.failed = result
                        error_class = "INTEGRATION_FAILED"
                        exit_code = EXIT_APPLY_PREFLIGHT_FAILED
                        break
                    state.completed[node.node_id] = result
                    state.integrated_paths_by_node[node.node_id] = set(result.changed_paths)

                if state.failed is not None:
                    # Stop launching new nodes, but wait for currently active nodes to exit
                    # so that temp worktrees can be cleaned. Active node results are not
                    # integrated after a failure.
                    if active:
                        concurrent.futures.wait(active.keys(), timeout=0.25, return_when=concurrent.futures.FIRST_COMPLETED)
                        continue
                    break

                if len(state.completed) == len(nodes):
                    break

                # Launch at most one new node per scheduling tick.
                active_nodes = list(active.values())
                now = time.monotonic()
                can_launch_by_gap = args.selftest_no_pacing or last_start == 0.0 or (now - last_start) >= args.min_start_gap_seconds
                if len(active) < args.max_parallel and len(state.launched_order) < args.max_total_calls and can_launch_by_gap:
                    candidate = next_ready_node(state, started=started, active_nodes=active_nodes)
                    if candidate is not None:
                        dep_ids = set(dependency_closure[candidate.node_id])
                        fut = executor.submit(
                            run_node,
                            repo=repo,
                            codex_path=codex_path,
                            task=task,
                            node=candidate,
                            template=template,
                            max_prompt_chars=args.max_prompt_chars,
                            max_raw_stdout_chars=args.max_raw_stdout_chars,
                            max_raw_stderr_chars=args.max_raw_stderr_chars,
                            max_semantic_output_chars=args.max_semantic_output_chars,
                            integration_worktree=integration_worktree,
                            dep_node_ids=dep_ids,
                            integrated_paths_by_node=dict(state.integrated_paths_by_node),
                        )
                        active[fut] = candidate
                        started.add(candidate.node_id)
                        state.launched_order.append(candidate.node_id)
                        state.max_simultaneous_observed = max(state.max_simultaneous_observed, len(active))
                        last_start = time.monotonic()
                        continue

                if len(state.launched_order) >= args.max_total_calls and len(state.completed) + len(active) < len(nodes):
                    exit_code = EXIT_CALL_BUDGET_EXCEEDED
                    error_class = "CALL_BUDGET_EXCEEDED"
                    break

                if active:
                    timeout = None
                    if not args.selftest_no_pacing and last_start:
                        remaining_gap = max(0.0, args.min_start_gap_seconds - (time.monotonic() - last_start))
                        timeout = min(0.25, remaining_gap) if remaining_gap else 0.25
                    concurrent.futures.wait(active.keys(), timeout=timeout, return_when=concurrent.futures.FIRST_COMPLETED)
                    continue

                reasons = blocked_ready_reasons(state, started=started, active_nodes=[])
                if reasons:
                    exit_code = EXIT_FLOW_BLOCKED
                    error_class = "FLOW_BLOCKED"
                    break
                exit_code = EXIT_FLOW_BLOCKED
                error_class = "FLOW_BLOCKED"
                break

        if exit_code == EXIT_SUCCESS and len(state.completed) == len(nodes):
            final_changed_paths = validate_final_apply(repo=repo, integration_worktree=integration_worktree, nodes=nodes)
            if args.apply:
                if git_status_porcelain(repo):
                    exit_code = EXIT_LIVE_WORKTREE_DIRTY
                    error_class = "LIVE_WORKTREE_DIRTY"
                else:
                    apply_final(repo=repo, integration_worktree=integration_worktree, changed_paths=final_changed_paths)
        return exit_code, error_class, state, integration_worktree, final_changed_paths
    finally:
        cleanup_errors: list[str] = []
        for wt in sorted([w for w in worktrees_to_cleanup if w], reverse=True):
            try:
                cleanup_worktree(repo, wt)
            except Exception as exc:
                cleanup_errors.append(str(exc))
        if cleanup_errors and exit_code == EXIT_SUCCESS:
            raise RuntimeError("; ".join(cleanup_errors))


def flow_output_text(state: FlowState, *, final_changed_paths: set[str], apply_requested: bool) -> str:
    lines: list[str] = []
    lines.append("chatgpt-codex-flow-orchestrator result")
    lines.append("")
    lines.append("Flow:")
    lines.append(f"- node ids: {', '.join(n.node_id for n in state.nodes)}")
    lines.append("")
    lines.append("Scheduling summary:")
    lines.append(f"- launched nodes: {', '.join(state.launched_order) if state.launched_order else '<none>'}")
    lines.append(f"- max simultaneous observed: {state.max_simultaneous_observed}")
    chained = [n.node_id for n in state.nodes if n.depends_on and n.node_id in state.completed]
    isolated = [n.node_id for n in state.nodes if not n.depends_on and n.node_id in state.completed]
    lines.append(f"- chained nodes completed: {', '.join(chained) if chained else '<none>'}")
    lines.append(f"- isolated nodes completed: {', '.join(isolated) if isolated else '<none>'}")
    lines.append("")
    lines.append("Changed files:")
    if final_changed_paths:
        for path in sorted(final_changed_paths):
            lines.append(f"- {path}")
    else:
        lines.append("- <none>")
    lines.append("")
    lines.append("Monitoring summary:")
    lines.append(f"- json events: {sum(r.json_events for r in state.completed.values())}")
    lines.append(f"- command executions: {sum(r.command_count for r in state.completed.values())}")
    lines.append(f"- file changes: {sum(r.file_change_count for r in state.completed.values())}")
    lines.append(f"- network noise lines: {state.network_noise_lines}")
    lines.append(f"- network noise bytes: {state.network_noise_bytes}")
    lines.append(f"- retryable network failures: {state.retryable_network_failures}")
    if state.failed:
        lines.append("")
        lines.append("Failure:")
        lines.append(f"- node: {state.failed.node_id}")
        lines.append(f"- error_class: {state.failed.error_class}")
        lines.append(f"- exit_code: {state.failed.exit_code}")
        if state.failed.out_of_scope_paths:
            lines.append(f"- out_of_scope_paths: {sorted(state.failed.out_of_scope_paths)}")
        if state.failed.stderr_semantic:
            lines.append(f"- stderr_semantic: {bounded(state.failed.stderr_semantic, 1000)}")
    lines.append("")
    lines.append("Validation needed:")
    lines.append("- inspect git diff")
    lines.append("- run deterministic wrapper/selftests")
    lines.append("- run project gates listed in the campaign handoff")
    lines.append("")
    lines.append("Parent action:")
    if state.failed:
        lines.append("- stop-for-operator | reject-as-out-of-scope | plan-new-flow-after-human-approval")
    elif apply_requested:
        lines.append("- inspect diff | validate | commit/push/PR")
    else:
        lines.append("- dry-run complete; rerun with --apply if accepted")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        default_effort = validate_effort(args.effort)
        default_model = validate_model(args.model)
        default_timeout = args.timeout if args.timeout is not None else EFFORT_TIMEOUT_DEFAULTS[default_effort]
        if default_timeout <= 0:
            return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message="timeout must be positive")
    except ValueError as exc:
        code = EXIT_CODEX_MODEL_INVALID if "model" in str(exc) else EXIT_CODEX_EFFORT_INVALID
        return fail(exit_code=code, error_class="INVALID_ARGS", message=str(exc))

    codex_path = resolve_executable(args.codex_executable)
    if not codex_path:
        return fail(exit_code=EXIT_CODEX_BINARY_MISSING, error_class="CODEX_BINARY_MISSING", message=f"could not resolve {args.codex_executable!r}")

    probe = probe_codex(codex_path)
    auth = auth_status(codex_path)
    if args.probe_only:
        emit_report(status="ok" if probe.get("supported") else "error", exit_code=0 if probe.get("supported") else EXIT_CODEX_UNSUPPORTED_FLAG, error_class=None if probe.get("supported") else "CODEX_UNSUPPORTED_FLAG", metadata={**probe, **auth})
        return 0 if probe.get("supported") else EXIT_CODEX_UNSUPPORTED_FLAG
    if not probe.get("supported"):
        return fail(exit_code=EXIT_CODEX_UNSUPPORTED_FLAG, error_class="CODEX_UNSUPPORTED_FLAG", message="codex exec is missing required flags", metadata=probe)
    if auth.get("auth_status") == "missing_or_invalid":
        return fail(exit_code=EXIT_CODEX_AUTH_MISSING_OR_INVALID, error_class="CODEX_AUTH_MISSING_OR_INVALID", message="codex login status indicates missing/invalid auth", metadata=auth)

    if not args.manifest:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message="--manifest is required unless --probe-only")

    try:
        repo = repo_root(args.cwd)
        if git_status_porcelain(repo):
            return fail(exit_code=EXIT_LIVE_WORKTREE_DIRTY, error_class="LIVE_WORKTREE_DIRTY", message="live repo must be clean before Stage C.1 flow")
        if args.max_parallel > 2:
            return fail(exit_code=EXIT_PARALLEL_LIMIT_EXCEEDED, error_class="PARALLEL_LIMIT_EXCEEDED", message="--max-parallel above 2 is forbidden")
        manifest = read_manifest(args.manifest)
        task, nodes, node_by_id, closure = normalize_manifest(
            manifest,
            repo=repo,
            default_model=default_model,
            default_effort=default_effort,
            default_timeout=default_timeout,
        )
        validate_caps(nodes=nodes, max_parallel=args.max_parallel, max_total_calls=args.max_total_calls, operator_approved=args.operator_approved_over_three_calls)
        template, template_path = load_template(args)
    except SymlinkPathRejected as exc:
        return fail(exit_code=EXIT_SYMLINK_PATH_REJECTED, error_class="SYMLINK_PATH_REJECTED", message=str(exc))
    except RuntimeError as exc:
        msg = str(exc)
        if "conflict" in msg or "collision" in msg:
            return fail(exit_code=EXIT_COLLISION_DETECTED, error_class="COLLISION_DETECTED", message=msg)
        if "approval" in msg or "approv" in msg or "max_total_calls" in msg or "three total Codex calls" in msg:
            return fail(exit_code=EXIT_CALL_BUDGET_EXCEEDED, error_class="CALL_BUDGET_EXCEEDED", message=msg)
        return fail(exit_code=EXIT_MANIFEST_INVALID, error_class="MANIFEST_INVALID", message=msg)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        return fail(exit_code=EXIT_MANIFEST_INVALID, error_class="MANIFEST_INVALID", message=str(exc))

    state_dir = Path(args.state_dir)
    lock = CallLock(state_dir)
    audit_status = "error"
    audit_exit = EXIT_WRAPPER_INTERNAL
    audit_error_class: str | None = "WRAPPER_INTERNAL"
    final_changed_paths: set[str] = set()
    flow_state: FlowState | None = None
    waited = 0

    try:
        lock.acquire()
        waited = enforce_flow_interval(state_dir, args.min_flow_interval_seconds, disabled=args.selftest_no_pacing)
        record_flow_start(state_dir, disabled=args.selftest_no_pacing, node_ids=[n.node_id for n in nodes])
        exit_code, error_class, flow_state, _integration_worktree, final_changed_paths = run_flow(
            repo=repo,
            codex_path=codex_path,
            task=task,
            nodes=nodes,
            node_by_id=node_by_id,
            dependency_closure=closure,
            template=template,
            args=args,
        )
        audit_status = "ok" if exit_code == EXIT_SUCCESS else "error"
        audit_exit = exit_code
        audit_error_class = error_class
        metadata = {
            "repo": repo,
            "apply": args.apply,
            "manifest_sha256": sha256_text(json.dumps(manifest, sort_keys=True)),
            "task_sha256": sha256_text(task),
            "node_ids": [n.node_id for n in nodes],
            "node_prompt_sha256": {n.node_id: sha256_text(n.prompt) for n in nodes},
            "template_path": str(template_path),
            "waited_seconds": waited,
            "max_parallel": args.max_parallel,
            "max_total_calls": args.max_total_calls,
            "operator_approved_over_three_calls": args.operator_approved_over_three_calls,
            "launched_nodes": flow_state.launched_order if flow_state else [],
            "completed_nodes": sorted(flow_state.completed) if flow_state else [],
            "max_simultaneous_observed": flow_state.max_simultaneous_observed if flow_state else 0,
            "network_noise_lines": flow_state.network_noise_lines if flow_state else 0,
            "network_noise_bytes": flow_state.network_noise_bytes if flow_state else 0,
            "retryable_network_failures": flow_state.retryable_network_failures if flow_state else 0,
            "changed_paths": sorted(final_changed_paths),
            "probe": probe,
            "auth_status": auth.get("auth_status"),
        }
        text = flow_output_text(flow_state, final_changed_paths=final_changed_paths, apply_requested=args.apply) if flow_state else ""
        emit_report(status=audit_status, exit_code=exit_code, error_class=error_class, metadata=metadata, text=text)
        return exit_code
    except SymlinkPathRejected as exc:
        audit_exit = EXIT_SYMLINK_PATH_REJECTED
        audit_error_class = "SYMLINK_PATH_REJECTED"
        return fail(exit_code=EXIT_SYMLINK_PATH_REJECTED, error_class="SYMLINK_PATH_REJECTED", message=str(exc))
    except Exception as exc:
        audit_exit = EXIT_WRAPPER_INTERNAL
        audit_error_class = "WRAPPER_INTERNAL"
        return fail(exit_code=EXIT_WRAPPER_INTERNAL, error_class="WRAPPER_INTERNAL", message=f"{type(exc).__name__}: {exc}")
    finally:
        try:
            record = {
                "timestamp_utc": utc_now_iso(),
                "status": audit_status,
                "exit_code": audit_exit,
                "error_class": audit_error_class,
                "manifest_path_sha256": sha256_text(str(Path(args.manifest).resolve())) if args.manifest else None,
                "manifest_sha256": sha256_text(Path(args.manifest).read_text(encoding="utf-8")) if args.manifest and Path(args.manifest).exists() else None,
                "node_ids": [n.node_id for n in nodes] if "nodes" in locals() else [],
                "node_prompt_sha256": {n.node_id: sha256_text(n.prompt) for n in nodes} if "nodes" in locals() else {},
                "network_noise_lines": flow_state.network_noise_lines if flow_state else 0,
                "network_noise_bytes": flow_state.network_noise_bytes if flow_state else 0,
                "retryable_network_failures": flow_state.retryable_network_failures if flow_state else 0,
                "changed_paths": sorted(final_changed_paths),
            }
            write_audit(args.audit_dir, record)
        except Exception:
            pass
        try:
            lock.release()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
