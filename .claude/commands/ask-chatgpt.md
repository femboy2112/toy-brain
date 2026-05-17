Spawn the `chatgpt-codex-subagent` agent to consult ChatGPT through the local Codex CLI wrapper.

Stage A is explicit, read-only, and advisory only.

Usage examples:

```text
/ask-chatgpt --mode plan --model <model> --effort high <prompt>
/ask-chatgpt --mode review --model <model> --effort medium <prompt>
/ask-chatgpt --mode summarize --model <model> --effort low <prompt>
/ask-chatgpt --mode debug --model <model> --effort high <prompt>
```

Rules:

- Use only Stage A modes: `plan`, `review`, `summarize`, `debug`.
- Do not use `code` mode.
- Do not apply Codex suggestions automatically.
- Do not invoke raw `codex` or `codex exec`.
- Invoke only:

```bash
python3 tools/claude_helpers/codex_chatgpt_subagent.py ...
```

- Report the wrapper status, Codex advisory output, and Claude's assessment.
- If Codex ignores the template, surface the raw output and tag `Confidence: unknown` and `Disagreement: unknown`.

The parent Claude session remains responsible for all edits, validation, staging, commit, and push.
