# PHASE3_11_LIVE_TEST_CORRIGENDA.md

## Purpose

Lock the test discipline that
`PHASE3_11_LIVE_TEST_KICKOFF.md` proposed. The corrigenda is the
decision document. Step 12 (live test matrix) reads from this
file; Steps 13-17 execute against the matrix and this corrigenda.

```text
Status: LOCKED / NO-IMPLEMENTATION
```

---

## 1. LOCKED: gating vs OBSERVED

```text
Gating observations (must succeed for the campaign to proceed):
  - --print-once exits 0 with the expected banner under each
    of: --llm-mode offline / mock / anthropic-api (no key) /
    claude-cli (no binary) / codex-cli (no binary)
  - --check-terminal exits 0 on the operator's platform
  - the offline /step path mutates BrainState as the kernel
    contract demands (tick advances, MSI updates, PtCns evaluates)
  - /save-session followed by --load-session reconstructs the
    same BrainState (Phase 3.9 cold-start continuity)
  - /db-status / /db-verify / /db-summary / /profile-summary /
    /stream-db-summary / /db-diff / /db-backup all execute with
    exit code 0 against a real saved session DB
  - --autosave-mode after-successful-mutation actually saves on
    /step and /stream-promote and does NOT save on read-only or
    failed dispatches
  - the catalog gate, citation verifier, import audit, and
    runner all stay green throughout Steps 13-17

OBSERVED-only observations (cannot fail the campaign):
  - real anthropic-api smoke (I-LLMTOG-14; requires API key)
  - real claude-cli smoke (I-LLMTOG-14; requires claude binary)
  - real codex-cli smoke (I-LLMTOG-18; requires codex binary)
  - any prose-level "feels nice / feels awkward" UX judgment

Rejected alternative: gating real-LLM smoke.
Rationale for rejection: the campaign cannot require external
tools to be available; that would make the campaign environment-
dependent and would conflate "kernel works" with "operator has
auth configured".
```

---

## 2. LOCKED: failure consequences

```text
If a GATING observation fails in Steps 13-17:

  (a) record the failure in the per-topic report
  (b) do NOT attempt a fix inside the live-test step (Step 13-17)
  (c) the Step 19 triage plan classifies the failure as
      critical correctness, safety/invariant, operator UX,
      documentation, or deferred enhancement
  (d) Step 20 is a hard review gate; no code-modifying fix is
      applied without explicit user acceptance of the Step 19
      triage plan
  (e) Step 21 may apply only the accepted critical correctness
      and safety/invariant fixes; UX and feature improvements
      move to a later campaign unless explicitly approved

If an OBSERVED observation fails (or is skipped):

  (a) record the observation in the per-topic report under
      "blocked by env" or "ORS skipped: <reason>"
  (b) do NOT classify it as a campaign failure
  (c) Step 18 aggregates it under "blocked by environment"

A campaign-blocking failure is ONLY a failure of:
  - the catalog gate
  - the citation verifier
  - the import audit
  - the invariant runner (REQUIRED red or STRUCTURAL red)
  - the four check_all.sh gates above

These are the same gates that the rest of the campaign uses.
The behavior tests do NOT add new gating gates beyond those.
```

---

## 3. LOCKED: confusing-behavior reporting wording

```text
Each per-topic report uses exactly one of these verdict words
per row in its observation table:

  works               observed behavior matches operator expectation
  awkward             observed behavior is correct but ergonomically poor
  confusing           observed output is hard to interpret without source
  fails               observed behavior is wrong (gating row only)
  missing             expected feature is not present
  blocked by env      external tool / auth absent; test could not run
  ORS skipped         real-LLM smoke skipped (sub-class of "blocked by env")

The Step 18 findings aggregate counts each verdict.
"fails" on a gating row triggers a Step 19 critical-correctness
classification.
```

---

## 4. LOCKED: handling missing claude / codex / anthropic-api

```text
When the external tool is missing:

  claude binary absent:
    --llm-mode claude-cli SST tests:
      MUST observe LlmRuntimeError naming the executable
      "claude" and the mode "claude-cli", exit code != 0
      from the entrypoint, no curses init, no DB writes.
      Verdict: "works" (the gating contract IS "missing
      executable fails before launch").
    --llm-mode claude-cli ORS tests:
      Verdict: "ORS skipped: claude not on PATH".

  codex binary absent:
    --llm-mode codex-cli SST tests:
      MUST observe LlmRuntimeError naming the executable
      "codex" and the mode "codex-cli", exit code != 0
      from the entrypoint, no curses init, no DB writes.
      Verdict: "works" (the gating contract IS "missing
      executable fails before launch"; I-LLMTOG-16).
    --llm-mode codex-cli ORS tests:
      Verdict: "ORS skipped: codex not on PATH".

  ANTHROPIC_API_KEY env / --llm-anthropic-api-key absent:
    --llm-mode anthropic-api SST tests:
      MUST observe LlmRuntimeError naming the API-key
      resolution failure, exit code != 0, no network.
      Verdict: "works" (gating; I-LLMTOG-05).
    --llm-mode anthropic-api ORS tests:
      Verdict: "ORS skipped: no API key configured".

Rejected alternative: skip the SST tests entirely when the
tool is absent.
Rationale for rejection: the "fails-closed-before-launch" SST
is the WHOLE POINT of the I-LLMTOG-05 / I-LLMTOG-06 / I-LLMTOG-16
gating rows. Running those SSTs without the tool is exactly how
you verify the fail-closed contract. The ORS smoke is the part
that requires the real tool.
```

---

## 5. LOCKED: temporary-DB cleanup contract

```text
All Step 13-17 session-db / backup-db paths follow the pattern:

  /tmp/phase3_11_<step_name>_<utc_nanos>/<file>.db

  Example:
    /tmp/phase3_11_persistence_1234567890123456789/sess.db
    /tmp/phase3_11_persistence_1234567890123456789/sess.db.bak

Cleanup rules:
  - each step that creates a temp dir MUST delete it before the
    step's commit, unless the step explicitly hands the dir to
    a later step (e.g., Step 14 creates a DB that Step 15 reads)
  - if a later step inherits the dir, the LAST step that uses it
    MUST delete it
  - if a step fails mid-execution, the temp dir is left in place
    and recorded in the report; the operator decides whether to
    delete it before re-running
  - no temp DB is committed to git
  - the .gitignore is NOT modified by Steps 13-17

Rejected alternative: use a per-step pytest tmp_path fixture.
Rationale for rejection: Steps 13-17 are not pytest; they are
operator-driven behavior reports. The /tmp pattern is uniform
and operator-readable.
```

---

## 6. LOCKED: per-step report-vs-implementation policy

```text
Steps 13-17 produce documentation only:

  Step 13 -> PHASE3_11_OFFLINE_INTERACTION_REPORT.md
  Step 14 -> PHASE3_11_PERSISTENCE_BEHAVIOR_REPORT.md
  Step 15 -> PHASE3_11_AUTOSAVE_BEHAVIOR_REPORT.md
  Step 16 -> PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
  Step 17 -> PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md

Each step may create at most ONE new markdown report. No step
edits source code under brain/, fixtures under brain/ui/fixtures/,
the catalog, or any guarded path. The temp-DB pattern is the
only filesystem write allowed.

If a Step 13-17 test reveals a critical correctness bug, the
operator records the finding and MOVES ON. The fix lives in
Step 21 after the Step 20 review gate accepts the Step 19
triage plan.

Rejected alternative: allow Step 13-17 to fix bugs inline.
Rationale for rejection: silent inline fixes erase the
evidence the campaign is trying to surface. The triage gate is
the explicit review point.
```

---

## 7. LOCKED: which operator-facing commands belong in which step

```text
Step 13 (offline interaction):
  --print-once               SST
  --check-terminal           SST
  full curses launch         MOT (TTY-dependent; may be skipped)
  /stream                    SST (driven via printable command line)
  /stream-summary            SST
  /stream-candidates         SST
  /stream-promote            SST
  /step                      SST
  /state                     SST
  /help                      RFI + SST
  /quit                      MOT (curses-only)

Step 14 (persistence):
  /save-session              SST
  /load-session              SST
  /session-status            SST
  cold start --load-session  SST
  session restore (profile + stream + last tick)  SST

Step 15 (autosave):
  --autosave-mode off (default)               SST
  --autosave-mode after-successful-mutation   SST
  /autosave-status                            SST
  /autosave-enable / /autosave-disable        SST
  read-only command does NOT autosave         SST
  failed command does NOT autosave            SST

Step 16 (DB observability + backup):
  /db-status                 SST
  --db-status one-shot       SST
  /db-verify                 SST
  --db-verify one-shot       SST
  /db-summary                SST
  /profile-summary           SST
  /stream-db-summary         SST
  /db-diff                   SST
  /db-backup                 SST
  --db-backup PATH one-shot  SST
  --db-backup-force overwrite gate  SST
  URI-scheme rejection       SST

Step 17 (LLM runtime):
  --llm-mode offline         SST  gating
  --llm-mode mock            SST  gating
  --llm-mode anthropic-api (no key)   SST  gating
  --llm-mode anthropic-api (with key) ORS  optional
  --llm-mode claude-cli (no binary)   SST  gating
  --llm-mode claude-cli (with binary) ORS  optional
  --llm-mode codex-cli (no binary)    SST  gating
  --llm-mode codex-cli (with binary)  ORS  optional
  --llm-enable-cache mode-gating      SST
  --print-once mode-independence      SST
```

Each step's report includes the commands actually run (the
above is the locked target; Section 2 of each report records
the actual subset run on the operator's platform).

---

## 8. LOCKED: report ID convention

```text
Each row in a per-topic report table uses an ID of the form:

  <step>.<topic>.<n>

Examples:
  13.print-once.1     first --print-once observation in Step 13
  14.save-load.3      third save-load observation in Step 14
  17.codex-cli.7      seventh codex-cli observation in Step 17

These IDs are referenced from the Step 18 findings aggregate
and the Step 19 triage plan.

Rejected alternative: re-use I-LLMTOG-* / I-PERSIST-* catalog IDs.
Rationale for rejection: the live behavior IDs describe observation
outcomes, not catalog rows. A catalog row may be green while a
specific operator experience is awkward; conflating them would
hide the awkwardness.
```

---

## 9. LOCKED: cross-platform expectations

```text
The behavior tests run on whatever the operator has:
  - Linux: SST + MOT + RFI all available
  - macOS: SST + MOT + RFI all available
  - Windows under WSL: SST + RFI available; MOT may be limited
  - non-TTY (CI shell): SST + RFI; MOT skipped with explicit
    "blocked by env: no TTY"

The Step 13-17 reports do NOT add OS-specific code paths.
They observe the existing code's behavior on the operator's
machine and record what they saw.

The Phase 3.11 campaign acceptance does NOT require all
platforms to be tested. One platform is sufficient. The
report's Environment section records which platform was used.
```

---

## 10. LOCKED: stop conditions during Steps 13-17

```text
Steps 13-17 stop and ask for user judgment when:

  - a gating row "fails" in a way that suggests on-disk
    state corruption (e.g., /save-session truncates the DB)
  - a behavior test wedges the operator's terminal in a way
    that cannot be recovered with Ctrl-C or `reset`
  - a behavior test reveals that an INVARIANT_CATALOG.md row's
    Python assertion is materially inaccurate
  - a behavior test reveals that an existing fixture's body
    is misaligned with the live entrypoint

In every other case, the step records the observation and
continues. The operator may always pause for review.
```

---

## 11. Next artifact

```text
PHASE3_11_LIVE_TEST_MATRIX.md   (Step 12)
```

The matrix enumerates the exact rows in the Section 7 list
above, assigns IDs per Section 8, and provides empty Expected /
Observed cells for the Step 13-17 reports to fill in.
