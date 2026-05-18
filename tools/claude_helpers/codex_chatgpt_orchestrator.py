#!/usr/bin/env python3
"""Stage C Codex orchestration wave runner for Claude Code.

Contract:
- Claude remains orchestrator/integrator.
- Runs one manifest wave with at most two Codex shards concurrently.
- Gives each Codex shard workspace-write only inside an isolated temp git worktree.
- Applies back only exact allowlisted files, after all shards pass scope checks.
- Rejects write/write and declared read/write collisions before Codex runs.
- Never stages, commits, pushes, restores, merges, or invokes shell=True.
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
from typing import Any, Mapping

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
EXIT_SHARD_FAILED = 43
EXIT_APPLY_PREFLIGHT_FAILED = 44

EFFORT_VALUES = {"low", "medium", "high"}
EFFORT_TIMEOUT_DEFAULTS = {"low": 180, "medium": 600, "high": 1200}
MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]+$")
DEFAULT_AUDIT_DIR = ".claude/codex_bridge_logs"
DEFAULT_STATE_DIR = ".claude/codex_bridge_state"
DEFAULT_MIN_WAVE_INTERVAL_SECONDS = 180
DEFAULT_MAX_PARALLEL = 2
DEFAULT_MAX_REAL_CALLS = 2
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


class SymlinkPathRejected(Exception):
    pass


@dataclass(frozen=True)
class Shard:
    shard_id: str
    prompt: str
    allowed_files: tuple[str, ...]
    read_files: tuple[str, ...] = ()
    allow_delete: tuple[str, ...] = ()
    model: str = "gpt-5.5"
    effort: str = "high"
    timeout: int = 1200


@dataclass
class ShardResult:
    shard_id: str
    exit_code: int
    error_class: str | None
    worktree: str
    stdout: str = ""
    stderr: str = ""
    codex_returncode: int | None = None
    changed_paths: set[str] = field(default_factory=set)
    out_of_scope_paths: set[str] = field(default_factory=set)
    json_events: int = 0
    agent_messages: list[str] = field(default_factory=list)
    command_count: int = 0
    file_change_count: int = 0
    duration_ms: int = 0


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds")


def bounded(value: str, limit: int = 5000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n...[truncated {len(value) - limit} chars]"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded Codex orchestration wave with up to two independent shards.")
    parser.add_argument("--manifest", help="JSON manifest defining exactly one orchestration wave")
    parser.add_argument("--cwd", default=".", help="Live repository root")
    parser.add_argument("--apply", action="store_true", help="Apply successful shard changes back to live repo")
    parser.add_argument("--model", default="gpt-5.5", help="Default model for shards")
    parser.add_argument("--effort", default="high", help="Default effort for shards: low, medium, high")
    parser.add_argument("--timeout", type=int, help="Default timeout seconds; defaults by effort")
    parser.add_argument("--max-parallel", type=int, default=DEFAULT_MAX_PARALLEL)
    parser.add_argument("--max-real-calls", type=int, default=DEFAULT_MAX_REAL_CALLS)
    parser.add_argument("--min-wave-interval-seconds", type=int, default=DEFAULT_MIN_WAVE_INTERVAL_SECONDS)
    parser.add_argument("--max-prompt-chars", type=int, default=80000)
    parser.add_argument("--max-output-chars", type=int, default=64000)
    parser.add_argument("--prompt-template", help="Optional worker template; defaults to prompts/orchestrate_worker.md")
    parser.add_argument("--audit-dir", default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    parser.add_argument("--codex-executable", default="codex")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--selftest-no-pacing", action="store_true")
    return parser.parse_args(argv)


def emit_report(*, status: str, exit_code: int, error_class: str | None, metadata: Mapping[str, Any], text: str = "") -> None:
    wrapper = {"status": status, "exit_code": exit_code, "error_class": error_class, **dict(metadata)}
    print("codex_chatgpt_orchestrator transport report")
    print()
    print("Wrapper metadata:")
    print(json.dumps(wrapper, indent=2, sort_keys=True))
    if text:
        print()
        print("Orchestration output:")
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
    return Path(__file__).resolve().parent / "prompts" / "orchestrate_worker.md"


def load_template(args: argparse.Namespace) -> tuple[str, Path]:
    template_path = Path(args.prompt_template) if args.prompt_template else default_template_path()
    return template_path.read_text(encoding="utf-8"), template_path


def read_manifest(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_manifest(manifest: dict[str, Any], *, repo: str, default_model: str, default_effort: str, default_timeout: int) -> tuple[str, list[Shard]]:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    task = manifest.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("manifest.task must be a non-empty string")
    waves = manifest.get("waves")
    if not isinstance(waves, list) or len(waves) != 1:
        raise ValueError("Stage C v1 accepts exactly one wave per invocation")
    wave = waves[0]
    if not isinstance(wave, dict):
        raise ValueError("manifest.waves[0] must be an object")
    shards_raw = wave.get("shards")
    if not isinstance(shards_raw, list) or not shards_raw:
        raise ValueError("manifest wave must contain at least one shard")
    shards: list[Shard] = []
    seen: set[str] = set()
    for idx, raw in enumerate(shards_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"shard {idx} must be an object")
        shard_id = raw.get("id")
        if not isinstance(shard_id, str) or not shard_id.strip():
            raise ValueError(f"shard {idx} requires non-empty id")
        if shard_id in seen:
            raise ValueError(f"duplicate shard id: {shard_id}")
        seen.add(shard_id)
        prompt = raw.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"shard {shard_id} requires non-empty prompt")
        allowed_raw = raw.get("allowed_files")
        if not isinstance(allowed_raw, list) or not allowed_raw:
            raise ValueError(f"shard {shard_id} requires non-empty allowed_files list")
        read_raw = raw.get("read_files", [])
        delete_raw = raw.get("allow_delete", [])
        if not isinstance(read_raw, list) or not isinstance(delete_raw, list):
            raise ValueError(f"shard {shard_id} read_files/allow_delete must be arrays")
        allowed = tuple(validate_path(str(p), repo=repo, label=f"allowed file for {shard_id}") for p in allowed_raw)
        reads = tuple(validate_path(str(p), repo=repo, label=f"read file for {shard_id}") for p in read_raw)
        deletes = tuple(validate_path(str(p), repo=repo, label=f"allow-delete file for {shard_id}") for p in delete_raw)
        if not set(deletes).issubset(set(allowed)):
            raise ValueError(f"shard {shard_id}: allow_delete paths must also be allowed_files")
        model = validate_model(str(raw.get("model", default_model)))
        effort = validate_effort(str(raw.get("effort", default_effort)))
        timeout = int(raw.get("timeout", default_timeout))
        if timeout <= 0:
            raise ValueError(f"shard {shard_id}: timeout must be positive")
        shards.append(Shard(shard_id=shard_id, prompt=prompt, allowed_files=allowed, read_files=reads, allow_delete=deletes, model=model, effort=effort, timeout=timeout))
    return task, shards


def collision_check(shards: list[Shard], *, max_parallel: int, max_real_calls: int) -> None:
    if max_parallel > 2:
        raise ValueError("max_parallel above 2 is not allowed in Stage C v1")
    if len(shards) > max_parallel:
        raise RuntimeError(f"wave has {len(shards)} shards but max_parallel={max_parallel}")
    if len(shards) > max_real_calls:
        raise RuntimeError(f"wave has {len(shards)} real calls but max_real_calls={max_real_calls}")
    all_writes: dict[str, str] = {}
    for shard in shards:
        for path in shard.allowed_files:
            if path in all_writes:
                raise RuntimeError(f"write/write collision on {path}: {all_writes[path]} and {shard.shard_id}")
            all_writes[path] = shard.shard_id
    for a in shards:
        reads = set(a.read_files)
        for b in shards:
            if a.shard_id == b.shard_id:
                continue
            overlap = reads.intersection(set(b.allowed_files))
            if overlap:
                raise RuntimeError(f"declared read/write collision: shard {a.shard_id} reads files written by shard {b.shard_id}: {sorted(overlap)}")


def build_prompt(template: str, *, task: str, shard: Shard, max_prompt_chars: int) -> str:
    allowed_block = "\n".join(f"- {p}" for p in shard.allowed_files)
    read_block = "\n".join(f"- {p}" for p in shard.read_files) if shard.read_files else "- <not declared>"
    delete_block = "\n".join(f"- {p}" for p in shard.allow_delete) if shard.allow_delete else "- <none>"
    prompt = (
        template.rstrip()
        + "\n\n---\n\n# Orchestration task\n\n"
        + task.strip()
        + "\n\n# Shard id\n\n"
        + shard.shard_id
        + "\n\n# Exact allowed files\n\n"
        + allowed_block
        + "\n\n# Declared read files\n\n"
        + read_block
        + "\n\n# Exact allowed deletions\n\n"
        + delete_block
        + "\n\n# Shard prompt\n\n"
        + shard.prompt.strip()
        + "\n"
    )
    if len(prompt) > max_prompt_chars:
        raise OverflowError(f"shard {shard.shard_id} prompt length {len(prompt)} exceeds {max_prompt_chars}")
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
        self.lock_path = state_dir / "orchestrator_inflight.lock"
        self.fd: int | None = None

    def acquire(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.fd, f"pid={os.getpid()} time={utc_now_iso()}\n".encode("utf-8"))
        except FileExistsError as exc:
            raise RuntimeError(f"another Codex orchestration wave is already in flight: {self.lock_path}") from exc

    def release(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def enforce_wave_interval(state_dir: Path, min_interval: int, *, disabled: bool) -> int:
    if disabled or min_interval <= 0:
        return 0
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "last_orchestrator_wave.json"
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


def record_wave_start(state_dir: Path, *, disabled: bool, shard_ids: list[str]) -> None:
    if disabled:
        return
    state_dir.mkdir(parents=True, exist_ok=True)
    data = {"timestamp_utc": utc_now_iso(), "monotonic": time.monotonic(), "pid": os.getpid(), "shard_ids": shard_ids}
    (state_dir / "last_orchestrator_wave.json").write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def setup_worktree(repo: str, shard_id: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", shard_id)
    temp_root = tempfile.mkdtemp(prefix=f"codex-orch-{safe_id}-")
    worktree = str(Path(temp_root) / "repo")
    proc = git(["worktree", "add", "--detach", worktree, "HEAD"], cwd=repo, timeout=120)
    if proc.returncode != 0:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise RuntimeError(f"git worktree add failed for shard {shard_id}: {bounded(proc.stderr)}")
    return worktree


def cleanup_worktree(repo: str, worktree: str) -> None:
    proc = git(["worktree", "remove", "--force", worktree], cwd=repo, timeout=120)
    parent = Path(worktree).parent
    shutil.rmtree(parent, ignore_errors=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git worktree remove failed: {bounded(proc.stderr)}")


def build_codex_argv(codex_path: str, *, shard: Shard, worktree: str) -> list[str]:
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
        shard.model,
        "-c",
        f"model_reasoning_effort={shard.effort}",
        "-",
    ]


def parse_json_events(stdout: str) -> tuple[int, list[str], int, int]:
    events = 0
    agent_messages: list[str] = []
    command_count = 0
    file_change_count = 0
    for lineno, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid Codex JSONL at line {lineno}: {exc}") from exc
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
                # tolerate schemas that carry final agent messages under item.completed
                if item2["text"] not in agent_messages:
                    agent_messages.append(item2["text"])
    return events, agent_messages, command_count, file_change_count


def run_shard(*, repo: str, codex_path: str, task: str, shard: Shard, template: str, max_prompt_chars: int, max_output_chars: int) -> ShardResult:
    start = time.monotonic()
    worktree = ""
    stdout = ""
    stderr = ""
    try:
        prompt = build_prompt(template, task=task, shard=shard, max_prompt_chars=max_prompt_chars)
        worktree = setup_worktree(repo, shard.shard_id)
        argv = build_codex_argv(codex_path, shard=shard, worktree=worktree)
        try:
            completed = subprocess.run(argv, input=prompt, capture_output=True, text=True, timeout=shard.timeout, check=False, cwd=worktree)
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            codex_returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            return ShardResult(shard_id=shard.shard_id, exit_code=EXIT_CODEX_TIMEOUT, error_class="CODEX_TIMEOUT", worktree=worktree, stderr=str(exc), duration_ms=int((time.monotonic() - start) * 1000))
        if len(stdout) > max_output_chars:
            return ShardResult(shard_id=shard.shard_id, exit_code=EXIT_CODEX_OUTPUT_TOO_LARGE, error_class="CODEX_OUTPUT_TOO_LARGE", worktree=worktree, stdout=bounded(stdout, 2000), stderr=stderr, codex_returncode=codex_returncode, duration_ms=int((time.monotonic() - start) * 1000))
        if codex_returncode != 0:
            err_class = "CODEX_NONZERO_EXIT"
            err_code = EXIT_CODEX_NONZERO_EXIT
            low = (stderr + "\n" + stdout).lower()
            if any(pat in low for pat in AUTH_PATTERNS):
                err_class = "CODEX_AUTH_MISSING_OR_INVALID"
                err_code = EXIT_CODEX_AUTH_MISSING_OR_INVALID
            return ShardResult(shard_id=shard.shard_id, exit_code=err_code, error_class=err_class, worktree=worktree, stdout=bounded(stdout, 2000), stderr=bounded(stderr, 5000), codex_returncode=codex_returncode, duration_ms=int((time.monotonic() - start) * 1000))
        try:
            events, agent_messages, command_count, file_change_count = parse_json_events(stdout)
        except ValueError as exc:
            return ShardResult(shard_id=shard.shard_id, exit_code=EXIT_JSON_PARSE_ERROR, error_class="JSON_PARSE_ERROR", worktree=worktree, stdout=bounded(stdout, 2000), stderr=str(exc), codex_returncode=codex_returncode, duration_ms=int((time.monotonic() - start) * 1000))
        temp_status = git_status_porcelain(worktree)
        changed_paths = parse_status_paths(temp_status)
        out_of_scope = changed_paths - set(shard.allowed_files)
        if out_of_scope:
            return ShardResult(shard_id=shard.shard_id, exit_code=EXIT_OUT_OF_SCOPE_DIFF, error_class="OUT_OF_SCOPE_DIFF", worktree=worktree, stdout=bounded(stdout, 2000), stderr=stderr, codex_returncode=codex_returncode, changed_paths=changed_paths, out_of_scope_paths=out_of_scope, json_events=events, agent_messages=agent_messages, command_count=command_count, file_change_count=file_change_count, duration_ms=int((time.monotonic() - start) * 1000))
        return ShardResult(shard_id=shard.shard_id, exit_code=EXIT_SUCCESS, error_class=None, worktree=worktree, stdout=stdout, stderr=stderr, codex_returncode=codex_returncode, changed_paths=changed_paths, json_events=events, agent_messages=agent_messages, command_count=command_count, file_change_count=file_change_count, duration_ms=int((time.monotonic() - start) * 1000))
    except SymlinkPathRejected as exc:
        return ShardResult(shard_id=shard.shard_id, exit_code=EXIT_SYMLINK_PATH_REJECTED, error_class="SYMLINK_PATH_REJECTED", worktree=worktree, stderr=str(exc), duration_ms=int((time.monotonic() - start) * 1000))
    except RuntimeError as exc:
        return ShardResult(shard_id=shard.shard_id, exit_code=EXIT_WORKTREE_SETUP_FAILED, error_class="WORKTREE_OR_RUNTIME_ERROR", worktree=worktree, stderr=str(exc), duration_ms=int((time.monotonic() - start) * 1000))


def validate_all_copybacks(*, repo: str, shards: list[Shard], results: list[ShardResult]) -> None:
    """Preflight: verify every shard's copy-back is safe BEFORE any live-repo write.

    Walks every changed path across all shard results and validates the
    write/delete that copy_allowed_changes would perform. Raises
    SymlinkPathRejected on symlink violations and RuntimeError on directory
    or undeclared-deletion violations. No live-repo file is modified here.
    """
    shard_by_id = {s.shard_id: s for s in shards}
    for result in results:
        shard = shard_by_id.get(result.shard_id)
        if shard is None:
            continue
        allowed = set(shard.allowed_files)
        allow_delete = set(shard.allow_delete)
        for path in sorted(result.changed_paths):
            if path not in allowed:
                raise RuntimeError(f"preflight: shard {shard.shard_id} change {path!r} is not in allowed_files")
            try:
                validate_path(path, repo=repo, label=f"apply target for {shard.shard_id}")
            except ValueError as exc:
                raise RuntimeError(f"preflight: {exc}") from exc
            src = Path(result.worktree) / path
            if src.is_symlink():
                raise SymlinkPathRejected(f"preflight: temp worktree source is a symlink: {path} (shard {shard.shard_id})")
            if src.exists():
                if src.is_dir():
                    raise RuntimeError(f"preflight: source is a directory; refusing to copy: {path} (shard {shard.shard_id})")
            else:
                if path not in allow_delete:
                    raise RuntimeError(f"preflight: Codex deleted {path} in shard {shard.shard_id}, but deletion was not explicitly allowed")


def copy_allowed_changes(*, repo: str, worktree: str, changed: set[str], allowed: set[str], allow_delete: set[str]) -> None:
    for path in sorted(changed):
        if path not in allowed:
            continue
        src = Path(worktree) / path
        dst = Path(repo) / path
        if src.is_symlink():
            raise SymlinkPathRejected(f"refusing to copy: temp worktree source is a symlink: {path}")
        if dst.is_symlink():
            raise SymlinkPathRejected(f"refusing to write: live repo destination is a symlink: {path}")
        if src.exists():
            if src.is_dir():
                raise RuntimeError(f"allowed path became directory; refusing to copy: {path}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            if path not in allow_delete:
                raise RuntimeError(f"Codex deleted {path}, but deletion was not explicitly allowed")
            if dst.exists():
                dst.unlink()


def cleanup_all(repo: str, results: list[ShardResult]) -> list[str]:
    errors: list[str] = []
    for result in results:
        if result.worktree:
            try:
                cleanup_worktree(repo, result.worktree)
            except RuntimeError as exc:
                errors.append(f"{result.shard_id}: {exc}")
    return errors


def summarize_results(results: list[ShardResult]) -> str:
    lines = ["codex orchestration wave report", ""]
    for result in results:
        lines.append(f"Shard {result.shard_id}:")
        lines.append(f"- exit_code: {result.exit_code}")
        lines.append(f"- error_class: {result.error_class}")
        lines.append(f"- changed_paths: {sorted(result.changed_paths)}")
        lines.append(f"- out_of_scope_paths: {sorted(result.out_of_scope_paths)}")
        lines.append(f"- json_events: {result.json_events}")
        lines.append(f"- command_count: {result.command_count}")
        lines.append(f"- file_change_count: {result.file_change_count}")
        if result.agent_messages:
            lines.append("- final_agent_message_excerpt:")
            lines.append(bounded(result.agent_messages[-1], 1000))
        if result.stderr:
            lines.append("- stderr_excerpt:")
            lines.append(bounded(result.stderr, 1000))
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    start = time.monotonic()
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else EXIT_INVALID_ARGS
    base_meta: dict[str, Any] = {"timestamp_utc": utc_now_iso(), "audit_dir": args.audit_dir, "state_dir": args.state_dir}
    try:
        default_effort = validate_effort(args.effort)
        default_model = validate_model(args.model)
    except ValueError as exc:
        code = EXIT_CODEX_MODEL_INVALID if "model" in str(exc) else EXIT_CODEX_EFFORT_INVALID
        return fail(exit_code=code, error_class="INVALID_ARGS", message=str(exc), metadata=base_meta)
    default_timeout = args.timeout if args.timeout is not None else EFFORT_TIMEOUT_DEFAULTS[default_effort]
    if args.max_parallel > 2:
        return fail(exit_code=EXIT_PARALLEL_LIMIT_EXCEEDED, error_class="PARALLEL_LIMIT_EXCEEDED", message="Stage C v1 max_parallel may not exceed 2", metadata=base_meta)
    codex_path = resolve_executable(args.codex_executable)
    if codex_path is None:
        return fail(exit_code=EXIT_CODEX_BINARY_MISSING, error_class="CODEX_BINARY_MISSING", message=f"codex executable not found: {args.codex_executable!r}", metadata=base_meta)
    try:
        live_repo = repo_root(str(Path(args.cwd).resolve()))
    except RuntimeError as exc:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message=str(exc), metadata=base_meta)
    try:
        probe = probe_codex(codex_path)
    except subprocess.TimeoutExpired as exc:
        return fail(exit_code=EXIT_CODEX_TIMEOUT, error_class="CODEX_TIMEOUT", message="codex probe timed out", metadata={**base_meta, "repo": live_repo}, text=str(exc))
    auth = auth_status(codex_path)
    meta_common: dict[str, Any] = {**base_meta, "repo": live_repo, "codex_path": codex_path, "codex_version": probe.get("codex_version"), "capabilities": probe.get("capabilities", {}), "unsupported": probe.get("unsupported", []), "max_parallel": args.max_parallel, "max_real_calls": args.max_real_calls, **auth}
    if args.probe_only:
        if not probe.get("supported"):
            return fail(exit_code=EXIT_CODEX_UNSUPPORTED_FLAG, error_class="CODEX_UNSUPPORTED_FLAG", message="installed codex lacks required Stage C flags", metadata=meta_common)
        if auth.get("auth_status") == "missing_or_invalid":
            return fail(exit_code=EXIT_CODEX_AUTH_MISSING_OR_INVALID, error_class="CODEX_AUTH_MISSING_OR_INVALID", message="codex is not authenticated", metadata=meta_common)
        emit_report(status="success", exit_code=0, error_class=None, metadata={**meta_common, "message": "codex orchestration probe passed"})
        return 0
    if not probe.get("supported"):
        return fail(exit_code=EXIT_CODEX_UNSUPPORTED_FLAG, error_class="CODEX_UNSUPPORTED_FLAG", message="installed codex lacks required Stage C flags", metadata=meta_common, text=probe.get("exec_help_excerpt", ""))
    if auth.get("auth_status") == "missing_or_invalid":
        return fail(exit_code=EXIT_CODEX_AUTH_MISSING_OR_INVALID, error_class="CODEX_AUTH_MISSING_OR_INVALID", message="codex is installed but not authenticated; run codex login", metadata=meta_common)
    if not args.manifest:
        return fail(exit_code=EXIT_MANIFEST_INVALID, error_class="MANIFEST_INVALID", message="--manifest is required unless --probe-only", metadata=meta_common)
    live_status = git_status_porcelain(live_repo)
    if live_status:
        return fail(exit_code=EXIT_LIVE_WORKTREE_DIRTY, error_class="LIVE_WORKTREE_DIRTY", message="live repo must be clean before orchestration apply", metadata={**meta_common, "live_status": live_status})
    try:
        manifest = read_manifest(args.manifest)
        task, shards = normalize_manifest(manifest, repo=live_repo, default_model=default_model, default_effort=default_effort, default_timeout=default_timeout)
        collision_check(shards, max_parallel=args.max_parallel, max_real_calls=args.max_real_calls)
        template, template_path = load_template(args)
    except SymlinkPathRejected as exc:
        return fail(exit_code=EXIT_SYMLINK_PATH_REJECTED, error_class="SYMLINK_PATH_REJECTED", message=str(exc), metadata=meta_common)
    except RuntimeError as exc:
        return fail(exit_code=EXIT_COLLISION_DETECTED, error_class="COLLISION_DETECTED", message=str(exc), metadata=meta_common)
    except (OSError, ValueError, json.JSONDecodeError, OverflowError) as exc:
        return fail(exit_code=EXIT_MANIFEST_INVALID, error_class="MANIFEST_INVALID", message=str(exc), metadata=meta_common)
    state_dir = Path(live_repo) / args.state_dir
    lock = CallLock(state_dir)
    results: list[ShardResult] = []
    cleanup_errors: list[str] = []
    waited_seconds = 0
    exit_code = EXIT_SUCCESS
    error_class: str | None = None
    apply_preflight_failed = False
    try:
        lock.acquire()
        waited_seconds = enforce_wave_interval(state_dir, args.min_wave_interval_seconds, disabled=args.selftest_no_pacing)
        record_wave_start(state_dir, disabled=args.selftest_no_pacing, shard_ids=[s.shard_id for s in shards])
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.max_parallel, len(shards))) as executor:
            futures = [executor.submit(run_shard, repo=live_repo, codex_path=codex_path, task=task, shard=shard, template=template, max_prompt_chars=args.max_prompt_chars, max_output_chars=args.max_output_chars) for shard in shards]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        # Deterministic result order for audit/apply/report.
        result_by_id = {r.shard_id: r for r in results}
        results = [result_by_id[s.shard_id] for s in shards]
        failed = [r for r in results if r.exit_code != EXIT_SUCCESS]
        if failed:
            exit_code = EXIT_SHARD_FAILED
            error_class = "SHARD_FAILED"
        if exit_code == EXIT_SUCCESS and args.apply:
            # All-or-nothing apply after every shard is clean. Preflight first;
            # only then copy back in manifest order.
            if git_status_porcelain(live_repo):
                exit_code = EXIT_LIVE_WORKTREE_DIRTY
                error_class = "LIVE_WORKTREE_DIRTY"
            else:
                try:
                    validate_all_copybacks(repo=live_repo, shards=shards, results=results)
                except SymlinkPathRejected as exc:
                    exit_code = EXIT_APPLY_PREFLIGHT_FAILED
                    error_class = "APPLY_PREFLIGHT_FAILED"
                    apply_preflight_failed = True
                    results.append(ShardResult(shard_id="apply_preflight", exit_code=exit_code, error_class=error_class, worktree="", stderr=str(exc)))
                except RuntimeError as exc:
                    exit_code = EXIT_APPLY_PREFLIGHT_FAILED
                    error_class = "APPLY_PREFLIGHT_FAILED"
                    apply_preflight_failed = True
                    results.append(ShardResult(shard_id="apply_preflight", exit_code=exit_code, error_class=error_class, worktree="", stderr=str(exc)))
                else:
                    try:
                        for shard, result in zip(shards, results):
                            copy_allowed_changes(repo=live_repo, worktree=result.worktree, changed=result.changed_paths, allowed=set(shard.allowed_files), allow_delete=set(shard.allow_delete))
                    except SymlinkPathRejected as exc:
                        exit_code = EXIT_SYMLINK_PATH_REJECTED
                        error_class = "SYMLINK_PATH_REJECTED"
                        results.append(ShardResult(shard_id="apply", exit_code=exit_code, error_class=error_class, worktree="", stderr=str(exc)))
                    except RuntimeError as exc:
                        exit_code = EXIT_APPLY_FAILED
                        error_class = "APPLY_FAILED"
                        results.append(ShardResult(shard_id="apply", exit_code=exit_code, error_class=error_class, worktree="", stderr=str(exc)))
    except RuntimeError as exc:
        return fail(exit_code=EXIT_RATE_LIMIT_STATE_ERROR, error_class="LOCK_OR_RATE_LIMIT_ERROR", message=str(exc), metadata=meta_common)
    finally:
        try:
            cleanup_errors = cleanup_all(live_repo, results)
        finally:
            lock.release()
    if cleanup_errors and exit_code == EXIT_SUCCESS:
        exit_code = EXIT_WORKTREE_CLEANUP_FAILED
        error_class = "WORKTREE_CLEANUP_FAILED"
    duration_ms = int((time.monotonic() - start) * 1000)
    prompts_hash = sha256_text(json.dumps({s.shard_id: s.prompt for s in shards}, sort_keys=True))
    audit = {
        **meta_common,
        "task_sha256": sha256_text(task),
        "shard_prompts_sha256": prompts_hash,
        "prompt_template_path": str(template_path),
        "prompt_template_sha256": sha256_text(template),
        "exit_code": exit_code,
        "error_class": error_class,
        "duration_ms": duration_ms,
        "waited_seconds": waited_seconds,
        "apply": args.apply,
        "apply_preflight_failed": apply_preflight_failed,
        "shards": [
            {
                "id": r.shard_id,
                "exit_code": r.exit_code,
                "error_class": r.error_class,
                "codex_returncode": r.codex_returncode,
                "changed_paths": sorted(r.changed_paths),
                "out_of_scope_paths": sorted(r.out_of_scope_paths),
                "json_events": r.json_events,
                "command_count": r.command_count,
                "file_change_count": r.file_change_count,
                "duration_ms": r.duration_ms,
            }
            for r in results
        ],
        "cleanup_errors": cleanup_errors,
    }
    try:
        write_audit(str(Path(live_repo) / args.audit_dir), audit)
    except OSError as exc:
        return fail(exit_code=EXIT_WRAPPER_INTERNAL, error_class="WRAPPER_INTERNAL", message=f"audit write failed: {exc}", metadata=meta_common)
    report = summarize_results(results)
    if cleanup_errors:
        report += "\nCleanup errors:\n" + "\n".join(f"- {e}" for e in cleanup_errors) + "\n"
    if exit_code != EXIT_SUCCESS:
        return fail(exit_code=exit_code, error_class=error_class or "ERROR", message=error_class or "orchestration failed", metadata={**meta_common, "duration_ms": duration_ms, "waited_seconds": waited_seconds}, text=report)
    emit_report(status="success", exit_code=0, error_class=None, metadata={**meta_common, "duration_ms": duration_ms, "waited_seconds": waited_seconds, "applied": args.apply}, text=report)
    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(EXIT_WRAPPER_INTERNAL)
