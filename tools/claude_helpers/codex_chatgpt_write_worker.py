#!/usr/bin/env python3
"""Limited-write Codex worker for Claude Code.

Stage B contract:
- separate from the Stage A read-only advisor wrapper;
- gives Codex workspace-write only inside a temporary detached git worktree;
- copies back only exact --allowed-file paths after scope checks;
- enforces sequential calls with a lock and minimum interval;
- never stages, commits, pushes, restores, or merges.
"""
from __future__ import annotations

import argparse
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
EXIT_JSON_PARSE_RESERVED = 30
EXIT_LIVE_WORKTREE_DIRTY = 31
EXIT_ALLOWED_PATH_INVALID = 32
EXIT_OUT_OF_SCOPE_DIFF = 33
EXIT_APPLY_FAILED = 34
EXIT_WORKTREE_SETUP_FAILED = 35
EXIT_WORKTREE_CLEANUP_FAILED = 36
EXIT_RATE_LIMIT_STATE_ERROR = 37

MODE_VALUES = {"write"}
EFFORT_VALUES = {"low", "medium", "high"}
EFFORT_TIMEOUT_DEFAULTS = {"low": 180, "medium": 600, "high": 1200}
MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]+$")
DEFAULT_AUDIT_DIR = ".claude/codex_bridge_logs"
DEFAULT_STATE_DIR = ".claude/codex_bridge_state"
DEFAULT_MIN_INTERVAL_SECONDS = 180
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


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds")


def bounded(value: str, limit: int = 5000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n...[truncated {len(value) - limit} chars]"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Codex as a limited-write worker in a temporary git worktree."
    )
    parser.add_argument("--mode", default="write", help="Stage B mode: write")
    parser.add_argument("--model", default="gpt-5.5", help="Model string passed to codex exec -m")
    parser.add_argument("--effort", default="high", help="Reasoning effort: low, medium, high")
    parser.add_argument("--cwd", default=".", help="Live repository root")
    parser.add_argument("--timeout", type=int, help="Timeout seconds; defaults by effort")
    parser.add_argument("--allowed-file", action="append", default=[], help="Exact repo-relative file path Codex may change; repeatable")
    parser.add_argument("--allow-delete", action="append", default=[], help="Exact allowlisted path Codex may delete; repeatable")
    parser.add_argument("--apply", action="store_true", help="Copy allowed changes from temp worktree back to live repo")
    parser.add_argument("--prompt-template", help="Optional template path; defaults to prompts/write.md")
    parser.add_argument("--prompt-file", help="Read user payload from this file; mutually exclusive with stdin payload")
    parser.add_argument("--max-prompt-chars", type=int, default=64000)
    parser.add_argument("--max-output-chars", type=int, default=32000)
    parser.add_argument("--audit-dir", default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    parser.add_argument("--min-interval-seconds", type=int, default=DEFAULT_MIN_INTERVAL_SECONDS)
    parser.add_argument("--codex-executable", default="codex")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--selftest-no-pacing", action="store_true", help="Disable sleep/write-rate checks for deterministic fake-codex tests only")
    return parser.parse_args(argv)


def emit_report(*, status: str, exit_code: int, error_class: str | None, metadata: Mapping[str, Any], codex_stdout: str = "", codex_stderr_excerpt: str = "") -> None:
    wrapper = {"status": status, "exit_code": exit_code, "error_class": error_class, **dict(metadata)}
    print("codex_chatgpt_write_worker transport report")
    print()
    print("Wrapper metadata:")
    print(json.dumps(wrapper, indent=2, sort_keys=True))
    print()
    if codex_stderr_excerpt:
        print("Codex stderr excerpt:")
        print(codex_stderr_excerpt)
        print()
    print("Codex stdout (verbatim):")
    print(codex_stdout, end="" if codex_stdout.endswith("\n") or not codex_stdout else "\n")


def fail(*, exit_code: int, error_class: str, message: str, metadata: Mapping[str, Any] | None = None, stderr_excerpt: str = "", stdout_excerpt: str = "") -> int:
    meta = dict(metadata or {})
    meta["message"] = message
    emit_report(status="error", exit_code=exit_code, error_class=error_class, metadata=meta, codex_stdout=stdout_excerpt, codex_stderr_excerpt=stderr_excerpt)
    return exit_code


def validate_mode(mode: str) -> str:
    if mode not in MODE_VALUES:
        raise ValueError(f"--mode must be one of {sorted(MODE_VALUES)}")
    return mode


def validate_effort(effort: str) -> str:
    if effort not in EFFORT_VALUES:
        raise ValueError(f"--effort must be one of {sorted(EFFORT_VALUES)}")
    return effort


def validate_model(model: str) -> str:
    if not model:
        raise ValueError("--model is required")
    if not MODEL_RE.match(model):
        raise ValueError("--model contains unsupported characters; allowed: A-Z a-z 0-9 . _ : / -")
    return model


def resolve_executable(executable: str) -> str | None:
    if os.path.sep in executable or (os.path.altsep and os.path.altsep in executable):
        path = Path(executable)
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(executable)


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


def validate_allowed_path(path_text: str, *, repo: str) -> str:
    if not path_text:
        raise ValueError("empty --allowed-file path")
    p = Path(path_text)
    if p.is_absolute():
        raise ValueError(f"absolute paths are not allowed: {path_text}")
    if any(part == ".." for part in p.parts):
        raise ValueError(f"parent traversal is not allowed: {path_text}")
    if p.parts and p.parts[0] == ".git":
        raise ValueError(f".git paths are not allowed: {path_text}")
    normalized = str(p.as_posix())
    if normalized in {".", ""}:
        raise ValueError(f"invalid path: {path_text}")
    live_path = Path(repo) / normalized
    if live_path.exists() and live_path.is_dir():
        raise ValueError(f"directories are not allowed as exact file paths: {path_text}")
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
    }
    required = ["config_override", "sandbox", "workspace_write", "ephemeral", "skip_git_repo_check", "model", "cd_flag"]
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


def stdin_payload() -> str | None:
    if sys.stdin.isatty():
        return None
    return sys.stdin.read()


def default_template_path() -> Path:
    return Path(__file__).resolve().parent / "prompts" / "write.md"


def read_prompt_parts(args: argparse.Namespace) -> tuple[str, str, Path]:
    template_path = Path(args.prompt_template) if args.prompt_template else default_template_path()
    template = template_path.read_text(encoding="utf-8")
    piped = stdin_payload()
    if args.prompt_file:
        if piped is not None and piped.strip():
            raise ValueError("provide user payload via exactly one of --prompt-file or stdin, not both")
        payload = Path(args.prompt_file).read_text(encoding="utf-8")
    else:
        if piped is None or not piped.strip():
            raise ValueError("user payload required via --prompt-file or stdin")
        payload = piped
    return template, payload, template_path


def build_combined_prompt(template: str, payload: str, *, allowed_files: list[str], allow_delete: set[str], max_prompt_chars: int) -> str:
    allowed_block = "\n".join(f"- {p}" for p in allowed_files)
    delete_block = "\n".join(f"- {p}" for p in sorted(allow_delete)) if allow_delete else "- <none>"
    combined = (
        template.rstrip()
        + "\n\n---\n\n# Exact allowed files\n\n"
        + allowed_block
        + "\n\n# Exact allowed deletions\n\n"
        + delete_block
        + "\n\n# User payload\n\n"
        + payload.strip()
        + "\n"
    )
    if len(combined) > max_prompt_chars:
        raise OverflowError(f"combined prompt length {len(combined)} exceeds --max-prompt-chars {max_prompt_chars}")
    return combined


def build_codex_argv(codex_path: str, *, model: str, effort: str, worktree: str) -> list[str]:
    return [
        codex_path,
        "exec",
        "--sandbox",
        "workspace-write",
        "--ephemeral",
        "--skip-git-repo-check",
        "--cd",
        worktree,
        "-m",
        model,
        "-c",
        f"model_reasoning_effort={effort}",
        "-",
    ]


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
        self.lock_path = state_dir / "inflight.lock"
        self.fd: int | None = None

    def acquire(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.fd, f"pid={os.getpid()} time={utc_now_iso()}\n".encode("utf-8"))
        except FileExistsError as exc:
            raise RuntimeError(f"another Codex bridge call is already in flight: {self.lock_path}") from exc

    def release(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def enforce_min_interval(state_dir: Path, min_interval: int, *, disabled: bool) -> int:
    if disabled or min_interval <= 0:
        return 0
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "last_real_call.json"
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


def record_real_call(state_dir: Path, *, disabled: bool) -> None:
    if disabled:
        return
    state_dir.mkdir(parents=True, exist_ok=True)
    data = {"timestamp_utc": utc_now_iso(), "monotonic": time.monotonic(), "pid": os.getpid()}
    (state_dir / "last_real_call.json").write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def setup_worktree(repo: str) -> str:
    temp_root = tempfile.mkdtemp(prefix="codex-write-worktree-")
    worktree = str(Path(temp_root) / "repo")
    proc = git(["worktree", "add", "--detach", worktree, "HEAD"], cwd=repo, timeout=120)
    if proc.returncode != 0:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise RuntimeError(f"git worktree add failed: {bounded(proc.stderr)}")
    return worktree


def cleanup_worktree(repo: str, worktree: str) -> None:
    proc = git(["worktree", "remove", "--force", worktree], cwd=repo, timeout=120)
    parent = Path(worktree).parent
    shutil.rmtree(parent, ignore_errors=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git worktree remove failed: {bounded(proc.stderr)}")


def copy_allowed_changes(*, repo: str, worktree: str, changed: set[str], allowed: set[str], allow_delete: set[str]) -> None:
    for path in sorted(changed):
        if path not in allowed:
            continue
        src = Path(worktree) / path
        dst = Path(repo) / path
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


def main(argv: list[str]) -> int:
    start = time.monotonic()
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else EXIT_INVALID_ARGS

    base_meta: dict[str, Any] = {"timestamp_utc": utc_now_iso(), "audit_dir": args.audit_dir, "state_dir": args.state_dir}

    try:
        mode = validate_mode(args.mode)
        effort = validate_effort(args.effort)
        model = validate_model(args.model)
    except ValueError as exc:
        code = EXIT_CODEX_MODEL_INVALID if "--model" in str(exc) else EXIT_INVALID_ARGS
        if "--effort" in str(exc):
            code = EXIT_CODEX_EFFORT_INVALID
        return fail(exit_code=code, error_class="INVALID_ARGS", message=str(exc), metadata=base_meta)

    timeout = args.timeout if args.timeout is not None else EFFORT_TIMEOUT_DEFAULTS[effort]
    codex_path = resolve_executable(args.codex_executable)
    if codex_path is None:
        return fail(exit_code=EXIT_CODEX_BINARY_MISSING, error_class="CODEX_BINARY_MISSING", message=f"codex executable not found: {args.codex_executable!r}", metadata=base_meta)

    try:
        live_repo = repo_root(str(Path(args.cwd).resolve()))
    except RuntimeError as exc:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message=str(exc), metadata=base_meta)

    try:
        allowed_files = [validate_allowed_path(p, repo=live_repo) for p in args.allowed_file]
        allow_delete = {validate_allowed_path(p, repo=live_repo) for p in args.allow_delete}
    except ValueError as exc:
        return fail(exit_code=EXIT_ALLOWED_PATH_INVALID, error_class="ALLOWED_PATH_INVALID", message=str(exc), metadata={**base_meta, "repo": live_repo})

    if not allowed_files and not args.probe_only:
        return fail(exit_code=EXIT_ALLOWED_PATH_INVALID, error_class="ALLOWED_PATH_INVALID", message="at least one --allowed-file is required", metadata={**base_meta, "repo": live_repo})
    allowed_set = set(allowed_files)
    if not allow_delete.issubset(allowed_set):
        return fail(exit_code=EXIT_ALLOWED_PATH_INVALID, error_class="ALLOWED_PATH_INVALID", message="every --allow-delete path must also be listed as --allowed-file", metadata={**base_meta, "repo": live_repo})

    try:
        probe = probe_codex(codex_path)
    except subprocess.TimeoutExpired as exc:
        return fail(exit_code=EXIT_CODEX_TIMEOUT, error_class="CODEX_TIMEOUT", message="codex probe timed out", metadata=base_meta, stderr_excerpt=str(exc))
    auth = auth_status(codex_path)
    meta_common = {
        **base_meta,
        "mode": mode,
        "model": model,
        "effort": effort,
        "timeout_seconds": timeout,
        "repo": live_repo,
        "codex_path": codex_path,
        "codex_version": probe.get("codex_version"),
        "capabilities": probe.get("capabilities", {}),
        "unsupported": probe.get("unsupported", []),
        "allowed_files": allowed_files,
        "allow_delete": sorted(allow_delete),
        "sandbox": "workspace-write",
        **auth,
    }

    if args.probe_only:
        if not probe.get("supported"):
            emit_report(status="error", exit_code=EXIT_CODEX_UNSUPPORTED_FLAG, error_class="CODEX_UNSUPPORTED_FLAG", metadata={**meta_common, "message": "installed codex lacks required Stage B flags"})
            return EXIT_CODEX_UNSUPPORTED_FLAG
        if auth.get("auth_status") == "missing_or_invalid":
            emit_report(status="error", exit_code=EXIT_CODEX_AUTH_MISSING_OR_INVALID, error_class="CODEX_AUTH_MISSING_OR_INVALID", metadata={**meta_common, "message": "codex is not authenticated"})
            return EXIT_CODEX_AUTH_MISSING_OR_INVALID
        emit_report(status="success", exit_code=0, error_class=None, metadata={**meta_common, "message": "codex limited-write probe passed"})
        return 0

    if not probe.get("supported"):
        return fail(exit_code=EXIT_CODEX_UNSUPPORTED_FLAG, error_class="CODEX_UNSUPPORTED_FLAG", message="installed codex lacks required Stage B flags", metadata=meta_common, stderr_excerpt=probe.get("exec_help_excerpt", ""))
    if auth.get("auth_status") == "missing_or_invalid":
        return fail(exit_code=EXIT_CODEX_AUTH_MISSING_OR_INVALID, error_class="CODEX_AUTH_MISSING_OR_INVALID", message="codex is installed but not authenticated; run codex login", metadata=meta_common, stderr_excerpt=str(auth.get("auth_detail", "")))

    live_status = git_status_porcelain(live_repo)
    if live_status:
        return fail(exit_code=EXIT_LIVE_WORKTREE_DIRTY, error_class="LIVE_WORKTREE_DIRTY", message="live repo must be clean before limited-write Codex apply", metadata={**meta_common, "live_status": live_status})

    try:
        template, payload, template_path = read_prompt_parts(args)
        combined_prompt = build_combined_prompt(template, payload, allowed_files=allowed_files, allow_delete=allow_delete, max_prompt_chars=args.max_prompt_chars)
    except (OSError, ValueError, RuntimeError) as exc:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message=str(exc), metadata=meta_common)
    except OverflowError as exc:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="PROMPT_TOO_LARGE", message=str(exc), metadata=meta_common)

    state_dir = Path(live_repo) / args.state_dir
    lock = CallLock(state_dir)
    worktree = ""
    stdout = ""
    stderr = ""
    codex_returncode: int | None = None
    changed_paths: set[str] = set()
    out_of_scope: set[str] = set()
    waited_seconds = 0
    applied = False

    try:
        lock.acquire()
        waited_seconds = enforce_min_interval(state_dir, args.min_interval_seconds, disabled=args.selftest_no_pacing)
        worktree = setup_worktree(live_repo)
        argv2 = build_codex_argv(codex_path, model=model, effort=effort, worktree=worktree)
        try:
            completed = subprocess.run(argv2, input=combined_prompt, capture_output=True, text=True, timeout=timeout, check=False, cwd=worktree)
            record_real_call(state_dir, disabled=args.selftest_no_pacing)
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            codex_returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            record_real_call(state_dir, disabled=args.selftest_no_pacing)
            duration_ms = int((time.monotonic() - start) * 1000)
            audit = {**meta_common, "prompt_sha256": sha256_text(combined_prompt), "prompt_chars": len(combined_prompt), "prompt_template_path": str(template_path), "prompt_template_sha256": sha256_text(template), "exit_code": EXIT_CODEX_TIMEOUT, "error_class": "CODEX_TIMEOUT", "duration_ms": duration_ms, "waited_seconds": waited_seconds, "stdout_bytes": 0, "stderr_bytes": 0, "changed_paths": [], "out_of_scope_paths": [], "applied": False}
            write_audit(str(Path(live_repo) / args.audit_dir), audit)
            return fail(exit_code=EXIT_CODEX_TIMEOUT, error_class="CODEX_TIMEOUT", message=f"codex exec timed out after {timeout}s", metadata={**meta_common, "waited_seconds": waited_seconds}, stderr_excerpt=str(exc))

        temp_status = git_status_porcelain(worktree)
        changed_paths = parse_status_paths(temp_status)
        out_of_scope = changed_paths - allowed_set

        if codex_returncode != 0:
            exit_code = EXIT_CODEX_NONZERO_EXIT
            error_class = "CODEX_NONZERO_EXIT"
            if any(p in (stderr + "\n" + stdout).lower() for p in AUTH_PATTERNS):
                exit_code = EXIT_CODEX_AUTH_MISSING_OR_INVALID
                error_class = "CODEX_AUTH_MISSING_OR_INVALID"
        elif len(stdout) > args.max_output_chars:
            exit_code = EXIT_CODEX_OUTPUT_TOO_LARGE
            error_class = "CODEX_OUTPUT_TOO_LARGE"
        elif out_of_scope:
            exit_code = EXIT_OUT_OF_SCOPE_DIFF
            error_class = "OUT_OF_SCOPE_DIFF"
        else:
            exit_code = EXIT_SUCCESS
            error_class = None

        if exit_code == EXIT_SUCCESS and args.apply:
            try:
                copy_allowed_changes(repo=live_repo, worktree=worktree, changed=changed_paths, allowed=allowed_set, allow_delete=allow_delete)
                applied = True
            except RuntimeError as exc:
                exit_code = EXIT_APPLY_FAILED
                error_class = "APPLY_FAILED"
                stderr = (stderr + "\n" + str(exc)).strip()

        duration_ms = int((time.monotonic() - start) * 1000)
        audit = {
            **meta_common,
            "prompt_sha256": sha256_text(combined_prompt),
            "prompt_chars": len(combined_prompt),
            "prompt_template_path": str(template_path),
            "prompt_template_sha256": sha256_text(template),
            "exit_code": exit_code,
            "error_class": error_class,
            "codex_returncode": codex_returncode,
            "duration_ms": duration_ms,
            "waited_seconds": waited_seconds,
            "stdout_bytes": len(stdout.encode("utf-8")),
            "stderr_bytes": len(stderr.encode("utf-8")),
            "changed_paths": sorted(changed_paths),
            "out_of_scope_paths": sorted(out_of_scope),
            "applied": applied,
        }
        write_audit(str(Path(live_repo) / args.audit_dir), audit)

        metadata = {**meta_common, "duration_ms": duration_ms, "waited_seconds": waited_seconds, "codex_returncode": codex_returncode, "changed_paths": sorted(changed_paths), "out_of_scope_paths": sorted(out_of_scope), "applied": applied}
        if exit_code != EXIT_SUCCESS:
            return fail(exit_code=exit_code, error_class=error_class or "ERROR", message=error_class or "limited-write Codex run failed", metadata=metadata, stderr_excerpt=bounded(stderr, 5000), stdout_excerpt=bounded(stdout, 2000))
        emit_report(status="success", exit_code=0, error_class=None, metadata=metadata, codex_stdout=stdout)
        return 0
    except RuntimeError as exc:
        return fail(exit_code=EXIT_WORKTREE_SETUP_FAILED if not worktree else EXIT_WRAPPER_INTERNAL, error_class="WORKTREE_OR_LOCK_ERROR", message=str(exc), metadata=meta_common)
    finally:
        cleanup_error = None
        if worktree:
            try:
                cleanup_worktree(live_repo, worktree)
            except RuntimeError as exc:
                cleanup_error = exc
        lock.release()
        if cleanup_error:
            print(f"WARNING: {cleanup_error}", file=sys.stderr)


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(EXIT_WRAPPER_INTERNAL)
