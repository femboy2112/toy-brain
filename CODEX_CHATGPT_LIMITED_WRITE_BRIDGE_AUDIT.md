# CODEX_CHATGPT_LIMITED_WRITE_BRIDGE_AUDIT.md

## Verdict

PASS — Stage B implementation, deterministic selftest, and repo gates all green on
`campaign/claude-chatgpt-codex-limited-write` (branched from `33c2f54`).
Real Codex write smoke deliberately NOT RUN — that requires explicit operator approval.

## Implemented scope

Stage B limited-write ChatGPT/Codex bridge:

- explicit `/ask-chatgpt-write` Claude command
- read-only `chatgpt-codex-writer` Claude agent that invokes only the wrapper
- isolated temp-worktree write wrapper
- exact `--allowed-file` copy-back boundary
- workspace-write only inside temp worktree
- no raw Codex allowlist
- no `danger-full-access`
- no staging, commit, push, restore, or merge by Codex wrapper
- sequential lock + min interval between real Codex calls

## Files changed

```text
.claude/agents/chatgpt-codex-writer.md
.claude/commands/ask-chatgpt-write.md
.claude/settings.json
.gitignore
tools/claude_helpers/codex_chatgpt_write_worker.py
tools/claude_helpers/codex_chatgpt_write_worker_selftest.py
tools/claude_helpers/prompts/write.md
CODEX_CHATGPT_LIMITED_WRITE_BRIDGE_AUDIT.md
```

## Capability probe

Local probe output (run before implementation):

```text
command -v codex:           /usr/local/bin/codex
codex --version:            codex-cli 0.130.0

codex exec --help required flags:
- -c / --config:            PRESENT  ("-c, --config <key=value>")
- --sandbox:                PRESENT  ("-s, --sandbox <SANDBOX_MODE>")
- workspace-write:          PRESENT  (sandbox possible values include
                                       read-only, workspace-write,
                                       danger-full-access)
- --ephemeral:              PRESENT
- --skip-git-repo-check:    PRESENT
- -m / --model:             PRESENT  ("-m, --model <MODEL>")
- --cd / -C:                PRESENT  ("-C, --cd <DIR>")
- stdin sentinel -:         PRESENT  ("If not provided as an argument
                                       (or if `-` is used), instructions
                                       are read from stdin")
```

Go/no-go: **GO**. Every required Stage B flag is supported by codex-cli 0.130.0.

## Wrapper invariants

```text
runs Codex only in temp git worktree:                   PASS  (setup_worktree creates a detached worktree from HEAD; codex exec is invoked with --cd <worktree>)
uses --sandbox workspace-write only in temp worktree:   PASS  (build_codex_argv passes "workspace-write" alongside --cd <worktree>)
requires exact --allowed-file list:                     PASS  (main() rejects empty list with EXIT_ALLOWED_PATH_INVALID=32 for non-probe runs)
rejects dirty live repo before apply:                   PASS  (selftest case_dirty returns 31 EXIT_LIVE_WORKTREE_DIRTY)
rejects out-of-scope temp changes:                      PASS  (selftest case_oos returns 33 EXIT_OUT_OF_SCOPE_DIFF; live repo bytes unchanged)
copies back only allowed files:                         PASS  (copy_allowed_changes iterates only changed ∩ allowed; selftest happy-path verifies)
never stages/commits/pushes:                            PASS  (no git add/commit/push/merge/restore call in wrapper source)
single lock prevents concurrent calls:                  PASS  (CallLock uses O_CREAT|O_EXCL on .claude/codex_bridge_state/inflight.lock)
min interval respected between real calls:              PASS  (enforce_min_interval sleeps until elapsed >= min_interval; --selftest-no-pacing reserved for fake tests only)
hash-only audit JSONL:                                  PASS  (selftest asserts prompt_sha256 present and the prompt text itself NOT in audit log)
```

## Selftest

```bash
python3 -m py_compile tools/claude_helpers/codex_chatgpt_write_worker.py
python3 tools/claude_helpers/codex_chatgpt_write_worker.py --help
python3 tools/claude_helpers/codex_chatgpt_write_worker_selftest.py
```

Result:

```text
py_compile:                                            PASS
--help:                                                PASS  (argparse usage rendered)
codex_chatgpt_write_worker_selftest:                   PASS
  (covers: happy-path allowed-file copy-back, out-of-scope rejection
   with live repo unchanged, dirty live worktree rejection,
   invalid-model rejection before subprocess, missing workspace-write
   capability rejection; audit JSONL hash-only check)
```

## Repo validation

```bash
python3 tools/claude_helpers/codex_chatgpt_subagent_selftest.py
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Result:

```text
codex_chatgpt_subagent_selftest:                       PASS
python3 -m tools.catalog counts:                       PASS  (259 / 86 / 12 / 15 / 16)
python3 -m tools.citations verify:                     PASS  (100 citations resolved)
python3 -m tools.import_audit:                         PASS  (I-PCE-05 clean)
python3 -m brain.invariants run:                       PASS  (353 rows; 0 gate failures)
bash tools/check_all.sh:                               PASS  (All checks passed.)
```

## Real Codex write smoke

Do not run unless operator explicitly approves in the active Claude Code session.

If approved, record:

```text
model:                  (not run — awaiting operator approval)
effort:
timeout:
allowed file:
result:
audit log:
gitignore:
```

## Safety summary

```text
No ToyI runtime files changed:                  OK   (brain/**, tools/catalog.py, brain/invariants.py untouched)
No raw codex allowlist:                         OK   (only Bash(python3 tools/claude_helpers/codex_chatgpt_write_worker.py:*) added)
No CURRENT_MISSION/CURRENT_CAMPAIGN edits:      OK
No runtime audit JSONL committed:               OK   (.claude/codex_bridge_logs/ already gitignored from Stage A)
No .claude/codex_bridge_state/ committed:       OK   (newly added to .gitignore)
No INVARIANT_CATALOG.md / catalog row changes:  OK
No lean_reference/scenarios/traces/docs/campaigns changes: OK
Out-of-scope fake write rejected by selftest:   OK   (exit 33 OUT_OF_SCOPE_DIFF; live repo bytes unchanged)
Limited write isolated to temp worktree:        OK   (setup_worktree + cleanup_worktree wrap every codex exec)
```
