#!/usr/bin/env python3
"""Claude -> Codex CLI -> ChatGPT advisory bridge.

Stage A contract:
- Transport + policy boundary only.
- Always invokes Codex read-only when asking the model.
- Does not parse or validate the semantic structure of Codex stdout.
- Emits wrapper metadata plus Codex stdout verbatim.
- Writes one compact audit JSONL record per invocation using one append write.
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
EXIT_CODEX_JSON_PARSE_ERROR = 30  # reserved; wrapper does not use JSON mode in Stage A

MODE_VALUES = {"plan", "review", "summarize", "debug"}
EFFORT_VALUES = {"low", "medium", "high"}
EFFORT_TIMEOUT_DEFAULTS = {"low": 60, "medium": 180, "high": 600}
MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]+$")
DEFAULT_AUDIT_DIR = ".claude/codex_bridge_logs"
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
UNKNOWN_COMMAND_PATTERNS = (
    "unrecognized subcommand",
    "unknown command",
    "invalid subcommand",
    "no such command",
    "usage:",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds")


def bounded(value: str, limit: int = 1000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n...[truncated {len(value) - limit} chars]"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invoke Codex CLI as a read-only ChatGPT advisory subagent for Claude Code."
    )
    parser.add_argument("--mode", help="Advisor mode: plan, review, summarize, debug")
    parser.add_argument("--model", help="Codex/OpenAI model string to pass to codex exec -m")
    parser.add_argument("--effort", default="medium", help="Reasoning effort: low, medium, high")
    parser.add_argument("--cwd", default=".", help="Repository/workspace root for Codex invocation")
    parser.add_argument("--timeout", type=int, help="Timeout seconds; defaults by effort")
    parser.add_argument("--max-prompt-chars", type=int, default=48000)
    parser.add_argument("--max-output-chars", type=int, default=16000)
    parser.add_argument("--prompt-template", help="Optional advisor template path; defaults by --mode")
    parser.add_argument("--prompt-file", help="Read user payload from this file. Mutually exclusive with stdin payload.")
    parser.add_argument("--audit-dir", default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--codex-executable", default="codex")
    parser.add_argument("--probe-only", action="store_true", help="Probe Codex capabilities and exit without invoking a model turn.")
    return parser.parse_args(argv)


def emit_report(
    *,
    status: str,
    exit_code: int,
    error_class: str | None,
    metadata: Mapping[str, Any],
    codex_stdout: str = "",
    codex_stderr_excerpt: str = "",
) -> None:
    wrapper = {
        "status": status,
        "exit_code": exit_code,
        "error_class": error_class,
        **dict(metadata),
    }
    print("codex_chatgpt_subagent wrapper transport report")
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


def fail(
    *,
    exit_code: int,
    error_class: str,
    message: str,
    metadata: Mapping[str, Any] | None = None,
    stderr_excerpt: str = "",
) -> int:
    meta = dict(metadata or {})
    meta["message"] = message
    emit_report(
        status="error",
        exit_code=exit_code,
        error_class=error_class,
        metadata=meta,
        codex_stdout="",
        codex_stderr_excerpt=stderr_excerpt,
    )
    return exit_code


def validate_mode(mode: str | None, *, probe_only: bool) -> str:
    if probe_only and mode is None:
        return "probe"
    if mode not in MODE_VALUES:
        raise ValueError(f"--mode must be one of {sorted(MODE_VALUES)}")
    return mode


def validate_effort(effort: str) -> str:
    if effort not in EFFORT_VALUES:
        raise ValueError(f"--effort must be one of {sorted(EFFORT_VALUES)}")
    return effort


def validate_model(model: str | None, *, probe_only: bool) -> str | None:
    if probe_only and not model:
        return None
    if not model:
        raise ValueError("--model is required unless --probe-only is used")
    if not MODEL_RE.match(model):
        raise ValueError("--model contains unsupported characters; allowed: A-Z a-z 0-9 . _ : / -")
    return model


def resolve_executable(executable: str) -> str | None:
    if os.path.sep in executable or (os.path.altsep and os.path.altsep in executable):
        path = Path(executable)
        return str(path) if path.is_file() and os.access(path, os.X_OK) else None
    return shutil.which(executable)


def run_small(args: list[str], *, timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def probe_codex(codex_path: str) -> dict[str, Any]:
    version_proc = run_small([codex_path, "--version"], timeout=10)
    version_text = (version_proc.stdout or version_proc.stderr).strip()

    help_proc = run_small([codex_path, "exec", "--help"], timeout=15)
    help_text = (help_proc.stdout or "") + "\n" + (help_proc.stderr or "")
    if help_proc.returncode != 0:
        return {
            "codex_version": version_text,
            "exec_help_returncode": help_proc.returncode,
            "exec_help_excerpt": bounded(help_text),
            "capabilities": {},
            "supported": False,
            "unsupported": ["exec_help"],
        }

    capabilities = {
        "config_override": ("-c" in help_text and ("--config" in help_text or "config" in help_text.lower())),
        "sandbox": "--sandbox" in help_text,
        "ephemeral": "--ephemeral" in help_text,
        "skip_git_repo_check": "--skip-git-repo-check" in help_text,
        "model": ("--model" in help_text or "-m" in help_text),
        "cd_flag": ("--cd" in help_text or " -C" in help_text or "-C," in help_text),
    }
    required = ["config_override", "sandbox", "ephemeral", "skip_git_repo_check", "model"]
    unsupported = [name for name in required if not capabilities.get(name)]
    return {
        "codex_version": version_text,
        "exec_help_returncode": help_proc.returncode,
        "capabilities": capabilities,
        "supported": not unsupported,
        "unsupported": unsupported,
    }


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
    if any(pat in low for pat in UNKNOWN_COMMAND_PATTERNS):
        return {"auth_status": "unknown", "auth_detail": "login status command not available or ambiguous"}
    return {"auth_status": "unknown", "auth_detail": bounded(text, 500)}


def stdin_payload() -> str | None:
    if sys.stdin.isatty():
        return None
    return sys.stdin.read()


def default_template_path(mode: str) -> Path:
    return Path(__file__).resolve().parent / "prompts" / f"{mode}.md"


def read_prompt_parts(args: argparse.Namespace, mode: str) -> tuple[str, str, Path]:
    template_path = Path(args.prompt_template) if args.prompt_template else default_template_path(mode)
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"failed to read prompt template {template_path}: {exc}") from exc

    piped = stdin_payload()
    if args.prompt_file:
        if piped is not None and piped.strip():
            raise ValueError("provide user payload via exactly one of --prompt-file or stdin, not both")
        try:
            payload = Path(args.prompt_file).read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(f"failed to read prompt file {args.prompt_file}: {exc}") from exc
    else:
        if piped is None or not piped.strip():
            raise ValueError("user payload required via --prompt-file or stdin")
        payload = piped
    return template, payload, template_path


def build_combined_prompt(template: str, payload: str, *, max_prompt_chars: int) -> str:
    combined = template.rstrip() + "\n\n---\n\n# User payload\n\n" + payload.strip() + "\n"
    if len(combined) > max_prompt_chars:
        raise OverflowError(f"combined prompt length {len(combined)} exceeds --max-prompt-chars {max_prompt_chars}")
    return combined


def build_codex_argv(codex_path: str, *, model: str, effort: str, cwd: str, capabilities: Mapping[str, Any]) -> list[str]:
    argv = [
        codex_path,
        "exec",
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--skip-git-repo-check",
        "-m",
        model,
        "-c",
        f"model_reasoning_effort={effort}",
    ]
    if capabilities.get("cd_flag"):
        argv.extend(["--cd", cwd])
    argv.append("-")
    return argv


def classify_nonzero(stderr: str, stdout: str) -> tuple[int, str]:
    low = (stderr + "\n" + stdout).lower()
    if any(pat in low for pat in AUTH_PATTERNS):
        return EXIT_CODEX_AUTH_MISSING_OR_INVALID, "CODEX_AUTH_MISSING_OR_INVALID"
    return EXIT_CODEX_NONZERO_EXIT, "CODEX_NONZERO_EXIT"


def audit_record_path(audit_dir: str) -> Path:
    date = _dt.datetime.now(tz=_dt.timezone.utc).date().isoformat()
    return Path(audit_dir) / f"{date}.jsonl"


def write_audit(audit_dir: str, record: Mapping[str, Any]) -> None:
    """Append one JSONL audit record with one write call.

    Invariant: serialize to one compact string ending in '\n', open in append
    mode, call f.write(record_line) exactly once. The resulting records remain
    well under ~4KB, so POSIX append writes are effectively atomic for the
    intended concurrent wrapper workload.
    """
    path = audit_record_path(audit_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)


def main(argv: list[str]) -> int:
    start = time.monotonic()
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else EXIT_INVALID_ARGS

    base_meta: dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "audit_dir": args.audit_dir,
    }

    try:
        mode = validate_mode(args.mode, probe_only=args.probe_only)
    except ValueError as exc:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message=str(exc), metadata=base_meta)
    try:
        effort = validate_effort(args.effort)
    except ValueError as exc:
        return fail(exit_code=EXIT_CODEX_EFFORT_INVALID, error_class="CODEX_EFFORT_INVALID", message=str(exc), metadata=base_meta)
    try:
        model = validate_model(args.model, probe_only=args.probe_only)
    except ValueError as exc:
        return fail(exit_code=EXIT_CODEX_MODEL_INVALID, error_class="CODEX_MODEL_INVALID", message=str(exc), metadata=base_meta)

    timeout = args.timeout if args.timeout is not None else EFFORT_TIMEOUT_DEFAULTS[effort]
    cwd = str(Path(args.cwd).resolve())
    if not Path(cwd).exists():
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message=f"--cwd does not exist: {cwd}", metadata=base_meta)

    codex_path = resolve_executable(args.codex_executable)
    if codex_path is None:
        return fail(
            exit_code=EXIT_CODEX_BINARY_MISSING,
            error_class="CODEX_BINARY_MISSING",
            message=f"codex executable not found: {args.codex_executable!r}",
            metadata={**base_meta, "mode": mode, "model": model, "effort": effort},
        )

    try:
        probe = probe_codex(codex_path)
    except subprocess.TimeoutExpired as exc:
        return fail(exit_code=EXIT_CODEX_TIMEOUT, error_class="CODEX_TIMEOUT", message="codex capability probe timed out", metadata=base_meta, stderr_excerpt=str(exc))
    except OSError as exc:
        return fail(exit_code=EXIT_CODEX_BINARY_MISSING, error_class="CODEX_BINARY_MISSING", message=str(exc), metadata=base_meta)

    auth = auth_status(codex_path)
    meta_common: dict[str, Any] = {
        **base_meta,
        "mode": mode,
        "model": model,
        "effort": effort,
        "timeout_seconds": timeout,
        "codex_path": codex_path,
        "codex_version": probe.get("codex_version"),
        "capabilities": probe.get("capabilities", {}),
        "unsupported": probe.get("unsupported", []),
        **auth,
    }

    if args.probe_only:
        if not probe.get("supported"):
            emit_report(
                status="error",
                exit_code=EXIT_CODEX_UNSUPPORTED_FLAG,
                error_class="CODEX_UNSUPPORTED_FLAG",
                metadata={**meta_common, "message": "installed codex lacks required Stage A flags; stop implementation"},
            )
            return EXIT_CODEX_UNSUPPORTED_FLAG
        if auth.get("auth_status") == "missing_or_invalid":
            emit_report(
                status="error",
                exit_code=EXIT_CODEX_AUTH_MISSING_OR_INVALID,
                error_class="CODEX_AUTH_MISSING_OR_INVALID",
                metadata={**meta_common, "message": "codex is installed but not authenticated; run codex login"},
            )
            return EXIT_CODEX_AUTH_MISSING_OR_INVALID
        emit_report(status="success", exit_code=0, error_class=None, metadata={**meta_common, "message": "codex capability probe passed"})
        return 0

    if not probe.get("supported"):
        return fail(
            exit_code=EXIT_CODEX_UNSUPPORTED_FLAG,
            error_class="CODEX_UNSUPPORTED_FLAG",
            message="installed codex lacks required Stage A flags; stop implementation",
            metadata=meta_common,
            stderr_excerpt=probe.get("exec_help_excerpt", ""),
        )
    if auth.get("auth_status") == "missing_or_invalid":
        return fail(
            exit_code=EXIT_CODEX_AUTH_MISSING_OR_INVALID,
            error_class="CODEX_AUTH_MISSING_OR_INVALID",
            message="codex is installed but not authenticated; run codex login",
            metadata=meta_common,
            stderr_excerpt=str(auth.get("auth_detail", "")),
        )

    try:
        template, payload, template_path = read_prompt_parts(args, mode)
        combined_prompt = build_combined_prompt(template, payload, max_prompt_chars=args.max_prompt_chars)
    except ValueError as exc:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="INVALID_ARGS", message=str(exc), metadata=meta_common)
    except OverflowError as exc:
        return fail(exit_code=EXIT_INVALID_ARGS, error_class="PROMPT_TOO_LARGE", message=str(exc), metadata=meta_common)
    except RuntimeError as exc:
        return fail(exit_code=EXIT_WRAPPER_INTERNAL, error_class="WRAPPER_INTERNAL", message=str(exc), metadata=meta_common)

    argv2 = build_codex_argv(
        codex_path,
        model=model or "",
        effort=effort,
        cwd=cwd,
        capabilities=probe.get("capabilities", {}),
    )
    stdout = ""
    stderr = ""
    returncode = None
    error_class = None
    exit_code = 0
    status = "success"
    truncated = False

    try:
        completed = subprocess.run(
            argv2,
            input=combined_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=cwd,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        audit = {
            **meta_common,
            "prompt_sha256": sha256_text(combined_prompt),
            "prompt_chars": len(combined_prompt),
            "prompt_template_path": str(template_path),
            "prompt_template_sha256": sha256_text(template),
            "exit_code": EXIT_CODEX_TIMEOUT,
            "error_class": "CODEX_TIMEOUT",
            "duration_ms": duration_ms,
            "stdout_bytes": 0,
            "stderr_bytes": 0,
            "truncated": False,
        }
        try:
            write_audit(args.audit_dir, audit)
        except OSError as audit_exc:
            return fail(exit_code=EXIT_WRAPPER_INTERNAL, error_class="WRAPPER_INTERNAL", message=f"audit write failed after timeout: {audit_exc}", metadata=meta_common)
        return fail(exit_code=EXIT_CODEX_TIMEOUT, error_class="CODEX_TIMEOUT", message=f"codex exec timed out after {timeout}s", metadata=meta_common, stderr_excerpt=str(exc))

    if returncode != 0:
        exit_code, error_class = classify_nonzero(stderr, stdout)
        status = "error"
    elif len(stdout) > args.max_output_chars:
        exit_code = EXIT_CODEX_OUTPUT_TOO_LARGE
        error_class = "CODEX_OUTPUT_TOO_LARGE"
        status = "error"
        truncated = True
    else:
        exit_code = EXIT_SUCCESS
        error_class = None
        status = "success"

    duration_ms = int((time.monotonic() - start) * 1000)
    audit = {
        **meta_common,
        "prompt_sha256": sha256_text(combined_prompt),
        "prompt_chars": len(combined_prompt),
        "prompt_template_path": str(template_path),
        "prompt_template_sha256": sha256_text(template),
        "exit_code": exit_code,
        "error_class": error_class,
        "codex_returncode": returncode,
        "duration_ms": duration_ms,
        "stdout_bytes": len(stdout.encode("utf-8")),
        "stderr_bytes": len(stderr.encode("utf-8")),
        "truncated": truncated,
    }
    try:
        write_audit(args.audit_dir, audit)
    except OSError as exc:
        return fail(exit_code=EXIT_WRAPPER_INTERNAL, error_class="WRAPPER_INTERNAL", message=f"audit write failed: {exc}", metadata=meta_common)

    metadata = {
        **meta_common,
        "duration_ms": duration_ms,
        "codex_returncode": returncode,
        "stdout_bytes": len(stdout.encode("utf-8")),
        "stderr_bytes": len(stderr.encode("utf-8")),
        "truncated": truncated,
    }
    if status == "error":
        message = error_class or "codex invocation failed"
        if exit_code == EXIT_CODEX_OUTPUT_TOO_LARGE:
            stdout_excerpt = bounded(stdout, 1000)
            emit_report(
                status="error",
                exit_code=exit_code,
                error_class=error_class,
                metadata={**metadata, "message": message, "stdout_excerpt": stdout_excerpt},
                codex_stdout="",
                codex_stderr_excerpt=bounded(stderr, 5000),
            )
            return exit_code
        emit_report(
            status="error",
            exit_code=exit_code,
            error_class=error_class,
            metadata={**metadata, "message": message},
            codex_stdout=bounded(stdout, 2000),
            codex_stderr_excerpt=bounded(stderr, 5000),
        )
        return exit_code

    emit_report(status="success", exit_code=EXIT_SUCCESS, error_class=None, metadata=metadata, codex_stdout=stdout)
    return EXIT_SUCCESS


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(EXIT_WRAPPER_INTERNAL)
