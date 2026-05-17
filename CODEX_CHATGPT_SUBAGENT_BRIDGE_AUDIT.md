# CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md

## Verdict

PASS for Stage A. Wrapper, agent, command, prompt templates, settings
allowlist, audit log gitignore, and deterministic fake-codex selftest are in
place. Real model-backed Codex invocation was deliberately not run; capability
probe against the real installed Codex passes.

## Implemented scope

Stage A ChatGPT/Codex advisory bridge:

- explicit `/ask-chatgpt` Claude command
- read-only `chatgpt-codex-subagent` Claude agent
- wrapper-bounded local Codex invocation (wrapper is the policy boundary)
- modes: plan / review / summarize / debug
- no code mode
- no ToyI runtime changes
- no raw Codex allowlist
- runtime audit JSONL gitignored at `.claude/codex_bridge_logs/`

## Files changed

```text
.claude/agents/chatgpt-codex-subagent.md
.claude/commands/ask-chatgpt.md
.claude/settings.json
.gitignore
tools/claude_helpers/codex_chatgpt_subagent.py
tools/claude_helpers/codex_chatgpt_subagent_selftest.py
tools/claude_helpers/prompts/plan.md
tools/claude_helpers/prompts/review.md
tools/claude_helpers/prompts/summarize.md
tools/claude_helpers/prompts/debug.md
CODEX_CHATGPT_SUBAGENT_BRIDGE_AUDIT.md
```

## Capability probe

Command output:

```text
command -v codex
/usr/local/bin/codex

codex --version
codex-cli 0.130.0

codex exec --help
  -c, --config <key=value>
  -m, --model <MODEL>
  -s, --sandbox <SANDBOX_MODE>   (read-only | workspace-write | danger-full-access)
  -C, --cd <DIR>
      --skip-git-repo-check
      --ephemeral
      --ignore-user-config
  codex exec - stdin sentinel supported
```

Required flags present:

```text
-c / --config:              PASS
--sandbox:                  PASS
--ephemeral:                PASS
--skip-git-repo-check:      PASS
-m / --model:               PASS
```

Auth status: `Logged in using ChatGPT` (auth_status=ok). Go/no-go: GO.

## Wrapper invariants

```text
wrapper forces --sandbox read-only:                         PASS
wrapper uses -c model_reasoning_effort=<effort>:            PASS
wrapper passes -m <model>:                                  PASS
wrapper caps prompt and output:                             PASS
wrapper returns Codex stdout verbatim under metadata:       PASS
wrapper does not parse semantic report sections:            PASS
wrapper writes hash-only audit JSONL:                       PASS
wrapper uses one append write per audit record:             PASS
wrapper rejects invalid model strings before subprocess:    PASS
wrapper validates mode and effort against fixed sets:       PASS
wrapper uses subprocess.run(..., shell=False):              PASS
```

## Exit code table

```text
0      success
1      wrapper internal error
2      invalid args
10     CODEX_BINARY_MISSING
11     CODEX_AUTH_MISSING_OR_INVALID
12     CODEX_UNSUPPORTED_FLAG
13     CODEX_MODEL_INVALID
14     CODEX_EFFORT_INVALID
20     CODEX_TIMEOUT
21     CODEX_NONZERO_EXIT
22     CODEX_OUTPUT_TOO_LARGE
30     CODEX_JSON_PARSE_ERROR (reserved)
```

## Selftest

```bash
python3 -m py_compile tools/claude_helpers/codex_chatgpt_subagent.py
python3 tools/claude_helpers/codex_chatgpt_subagent.py --help
python3 tools/claude_helpers/codex_chatgpt_subagent_selftest.py
```

Result:

```text
py_compile: PASS
--help:     PASS (argparse usage rendered)
selftest:   codex_chatgpt_subagent_selftest: PASS
  - probe-only against fake codex: exit 0
  - happy path: exit 0; argv contains --sandbox read-only, --ephemeral,
    --skip-git-repo-check, -m <model>, -c model_reasoning_effort=low,
    trailing '-' stdin sentinel
  - invalid model: exit 13 / CODEX_MODEL_INVALID
  - missing -c support: exit 12 / CODEX_UNSUPPORTED_FLAG
  - auth failure: exit 11 / CODEX_AUTH_MISSING_OR_INVALID
  - oversized output: exit 22 / CODEX_OUTPUT_TOO_LARGE
  - timeout: exit 20 / CODEX_TIMEOUT
  - audit JSONL contains prompt_sha256 / prompt_template_sha256, not prompt text
```

## Repo validation

```bash
python3 -m tools.catalog counts
python3 -m tools.citations verify
python3 -m tools.import_audit
python3 -m brain.invariants run
bash tools/check_all.sh
```

Result:

```text
catalog counts:        REQUIRED 240 / STRUCTURAL 85 / NOT-EXERCISED 11 /
                       DEFERRED 14 / OBSERVED 16 — all ok
citations verify:      Verified 100 citations; all resolve in lean_reference/
import_audit:          I-PCE-05: agency.py is clean of pce imports
brain.invariants run:  333 rows checked, REQUIRED red: 0, STRUCTURAL red: 0,
                       gate failures: 0
check_all.sh:          All checks passed
```

## Manual real Codex smoke

Status:

```text
PASS — operator approved and executed
```

Record:

```text
model:   gpt-5.5
                 (gpt-5.1-codex, gpt-5, gpt-5-codex, gpt-5.1, o3, gpt-4o
                  rejected by the ChatGPT-account Codex backend with HTTP 400
                  "model is not supported when using Codex with a ChatGPT account")
effort:  low
timeout: 120s
command: printf "Return a valid Stage A summarize advisory report. In the
         Answer section, say exactly: hello from bridge\n" \
         | python3 tools/claude_helpers/codex_chatgpt_subagent.py \
           --mode summarize --model gpt-5.5 --effort low --timeout 120
exit:    0
notes:
  - wrapper transport report rendered; Codex stdout surfaced verbatim under
    the wrapper metadata block
  - Codex returned the full Stage A summarize template; Answer section read
    exactly: "hello from bridge"
  - runtime audit JSONL appended at .claude/codex_bridge_logs/2026-05-17.jsonl
    with prompt_sha256 + prompt_template_sha256 (no prompt content)
  - .claude/codex_bridge_logs/ is gitignored; the audit log was not staged
  - the wrapper's error-path stderr display bound was widened from 1000 to
    5000 chars during smoke diagnosis; this is the only tracked-file change
    beyond the original Stage A drop
```

## Remaining work

Stage B, not implemented here:

```text
/go --advisor=chatgpt integration
formal disagreement protocol during mission execution
optional code mode as patch-sketch only
```

Stage C, not implemented here:

```text
write-capable Codex shard behind explicit operator approval, exact file list, and diff guard
```
