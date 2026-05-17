# PHASE3_11_CODEX_CLI_RUNTIME_CATALOG_PATCH_PLAN.md

## Purpose

Bind every row, count, citation, and EXPECTED_COUNTS update that
the Step 8 catalog patch will apply when (and only when) the
Step 7 review gate A accepts this plan. This is a planning
artifact only; it does not edit `INVARIANT_CATALOG.md`,
`tools/catalog.py`, `brain/_catalog_ids.py`, `brain/invariants.py`,
`brain/ui/llm_runtime.py`, `brain/llm/client.py`,
`brain/ui/__main__.py`, or any guarded path.

The plan reads from the locked decisions in
`PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md` (Step 5).
The Step 7 review gate A reads from this document and the
corrigenda together.

```text
Status: LOCKED / REVIEW-GATED / NO-IMPLEMENTATION-YET
```

Hard rule (unchanged):

```text
Do not apply this patch (Step 8) or implement the runtime (Step 9)
until the Step 7 review gate A explicitly accepts this plan.
```

---

## 1. Patch context

Predecessor patch:

```text
Phase 3.10c Autosave Policy (Step 17 commit landed in PR #9;
v0.18 -> v0.19; +11 REQUIRED, +4 STRUCTURAL, +1 OBSERVED,
-1 NOT-EXERCISED). Integrated audit PASS.
```

Accepted Phase 3.11 planning artifacts at HEAD of campaign branch:

```text
PHASE3_11_COMPREHENSIVE_LIVE_BEHAVIOR_TEST_ROADMAP.md (on main)
PHASE3_11_COMPREHENSIVE_BEHAVIOR_TEST_SYNTHESIS.md
PHASE3_11_CODEX_CLI_RUNTIME_SYNTHESIS.md
PHASE3_11_CODEX_CLI_RUNTIME_KICKOFF.md
PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md
```

---

## 2. Patch impact

```text
+ 2 REQUIRED       (I-LLMTOG-16, I-LLMTOG-17)
+ 0 STRUCTURAL     (I-LLMTOG-12 body updates in place)
+ 0 NOT-EXERCISED
+ 0 DEFERRED
+ 1 OBSERVED       (I-LLMTOG-18)
```

Expected counts after this accepted patch (v0.20):

```text
Catalog version:  v0.20
REQUIRED:        214
STRUCTURAL:       83
NOT-EXERCISED:     9
DEFERRED:         12
OBSERVED:         16
Total tabular:   334
```

No existing row is retired. No existing row is renamed. The
I-LLMTOG-12 row's body text is updated to assert exactly 5
members (was 4); its row ID, position, status, source kind, and
fixture binding remain unchanged.

No I-PERSIST-* row, I-AUTOSAVE-* row, I-UI-* row, I-UISTRM-* row,
I-AGN-* row, or any non-LLMTOG row is touched by this patch.

---

## 3. New row bodies (verbatim text for INVARIANT_CATALOG.md)

Format follows the existing I-LLMTOG-* table convention (one row
per line in the markdown table). Pipe-separated columns:

```text
| ID | Source | Proposition | Python assertion | Module | Fixture | Status |
```

### 3.1 I-LLMTOG-16 (NEW, REQUIRED)

```text
| I-LLMTOG-16 | Engineering hypothesis (Phase 3.11 Codex CLI Runtime Option) | `CODEX_CLI` without executable raises before launch. | `build_llm_client_from_config(LlmRuntimeConfig(mode=LlmRuntimeMode.CODEX_CLI, codex_cli_executable="<not-on-path>"))` raises `LlmRuntimeError` naming the missing executable and the mode; no `CodexCLIClient` instance is returned; the factory does not consult credential / configuration env vars (PATH lookup is confined to `_which` for executable resolution). | `brain/ui/llm_runtime.py` | `llm_runtime_codex_cli_requires_executable.py` | REQUIRED |
```

Mirrors I-LLMTOG-06 exactly; only the mode / class names differ.

### 3.2 I-LLMTOG-17 (NEW, REQUIRED)

```text
| I-LLMTOG-17 | Engineering hypothesis (Phase 3.11 Codex CLI Runtime Option) | `CODEX_CLI` factory returns the documented backend without invoking it. | `build_llm_client_from_config(LlmRuntimeConfig(mode=LlmRuntimeMode.CODEX_CLI, codex_cli_executable=sys.executable))` returns an instance of `CodexCLIClient` whose `command[0]` is the resolved executable path; no subprocess call is performed at factory time; the fixture asserts construction only and must not invoke `eval_consistency`. | `brain/ui/llm_runtime.py` | `llm_runtime_codex_cli_factory.py` | REQUIRED |
```

Mirrors I-LLMTOG-03's "construction only" clause for the
codex-cli-specific factory path.

### 3.3 I-LLMTOG-18 (NEW, OBSERVED)

```text
| I-LLMTOG-18 | Engineering hypothesis (Phase 3.11 Codex CLI Runtime Option) | Optional real `codex-cli` smoke walk. | A documented out-of-band smoke walk that launches `python3 -m brain.ui --llm-mode codex-cli --llm-codex-cli-executable <path> --print-once` records successful exit, then a full session that issues `/stream <text>`, `/stream-promote`, and `/step` records exactly one `subprocess.run` invocation against the locked command tuple `("codex", "exec")`, a bounded `stderr` surface, and the bounded `status_message` outcome of the `LLMClient` call; the row is OBSERVED and cannot fail the runner; the walk is documented in `PHASE3_11_CODEX_CLI_RUNTIME_CORRIGENDA.md` Section 11 and is recorded by the operator in `PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md`. | `brain/ui/llm_runtime.py` | (none) | OBSERVED |
```

Mirrors I-LLMTOG-14's OBSERVED-only discipline.

---

## 4. Existing row body update (I-LLMTOG-12)

Current body (catalog line 620, verbatim):

```text
| I-LLMTOG-12 | Engineering hypothesis (Phase 3.8b LLM Runtime Toggle) | `LlmRuntimeMode` is a finite closed `str, Enum`. | `LlmRuntimeMode` is a `(str, Enum)` subclass whose members are exactly the documented four values; the membership set is the same as the runtime audit in I-LLMTOG-02 but the check is STRUCTURAL because the enumeration shape (`str, Enum`, finite member list) is the assertion under test. | `brain/ui/llm_runtime.py` | `llm_runtime_mode_closed.py` | STRUCTURAL |
```

Updated body (Step 8 writes this verbatim):

```text
| I-LLMTOG-12 | Engineering hypothesis (Phase 3.8b LLM Runtime Toggle; extended in Phase 3.11 Codex CLI Runtime Option) | `LlmRuntimeMode` is a finite closed `str, Enum`. | `LlmRuntimeMode` is a `(str, Enum)` subclass whose members are exactly the documented five values (`OFFLINE`, `MOCK`, `ANTHROPIC_API`, `CLAUDE_CLI`, `CODEX_CLI`); the membership set is the same as the runtime audit in I-LLMTOG-02 (extended) but the check is STRUCTURAL because the enumeration shape (`str, Enum`, finite member list) is the assertion under test. | `brain/ui/llm_runtime.py` | `llm_runtime_mode_closed.py` | STRUCTURAL |
```

Diff summary:

```text
- "documented four values"   -> "documented five values
                                  (OFFLINE, MOCK, ANTHROPIC_API,
                                  CLAUDE_CLI, CODEX_CLI)"
- "the runtime audit in I-LLMTOG-02"
                              -> "the runtime audit in
                                  I-LLMTOG-02 (extended)"
- Source field appended with
  "; extended in Phase 3.11 Codex CLI Runtime Option"
- Row ID, Status, Module, Fixture: UNCHANGED.
```

No other existing row body changes. The fixture extensions
listed in corrigenda Section 10 happen in Step 9 implementation;
the catalog text for those rows already covers codex-cli
implicitly via phrasing like "each accepted mode", "model-backed
modes", "each combo", and "the LLM runtime surface".

---

## 5. Catalog version banner update

The v0.20 banner at the top of `INVARIANT_CATALOG.md` (current
v0.19 banner at line 11; new banner is appended above it per the
existing patch-history convention) reads:

```text
> **Catalog version:** v0.20. Patches over v0.19 (Phase 3.11
> Codex CLI Runtime Option catalog expansion): +2 REQUIRED rows,
> +1 OBSERVED row, +0 STRUCTURAL/NOT-EXERCISED/DEFERRED rows. Adds
> the `I-LLMTOG-16..I-LLMTOG-18` extension to the existing Phase
> 3.8b `I-LLMTOG-*` family: `CODEX_CLI` is added as the fifth
> `LlmRuntimeMode` member (`"codex-cli"` value, appended after
> `CLAUDE_CLI`); the factory `build_llm_client_from_config`
> dispatches `CODEX_CLI` to a new helper `_build_codex_cli_client`
> that resolves `codex_cli_executable` via `_which`, raises
> `LlmRuntimeError` naming the missing executable when the
> resolution fails, and otherwise returns a `CodexCLIClient`
> (frozen / slots `dataclass` in `brain/llm/client.py`) whose
> default `command` tuple is `("codex", "exec")` and whose
> `timeout_seconds` is shared with the existing `--llm-timeout`
> flag; a new `--llm-codex-cli-executable` CLI flag selects the
> executable (default `"codex"`); the `parse_llm_runtime_args`
> helper accepts `--llm-mode codex-cli` and `BRAIN_LLM_MODE=codex-cli`
> as explicit opt-in routes; the cache wrapping rule extends
> (`CODEX_CLI` + `enable_cache` returns a `CachedClient` wrapping
> `CodexCLIClient`); the `--print-once` independence rule
> extends; the explicit-opt-in rule extends (environment-only
> auto-selection is rejected); the tick seam rule extends
> (selected `CodexCLIClient` enters `tick()` through the existing
> `run_curses(session, client=..., ...)` argument with no second
> classification path); the static AST audit extends (the
> import set for `brain/ui/llm_runtime.py` and `brain/llm/client.py`
> remains bounded and rejects `curses`, `brain.tlica`, `brain.tick`,
> and anything outside the documented seam set); the `LlmRuntimeConfig`
> frozen / slots assertion extends with `codex_cli_executable: str`
> as the only new field; an optional real `codex-cli` smoke walk
> (I-LLMTOG-18) is OBSERVED and cannot fail the runner. The
> I-LLMTOG-12 STRUCTURAL row body updates its member-count
> assertion from four to five. These rows are engineering
> hypotheses, not Lean theorem claims. They do not authorize
> a non-offline default, automatic codex auto-detection without
> opt-in, an environment read inside `build_llm_client_from_config`,
> a new `LLMClient` implementation beyond the five shipped
> backends, a second classification path, model-backed scoring of
> stream evidence, a new persistence schema, a new autosave
> trigger, a new operator verb, or any TLICA runtime mutation.
> The Phase 3.11 Codex CLI Runtime Option introduces one operator-
> facing CLI surface (`--llm-codex-cli-executable PATH`) and one
> enum value (`codex-cli`); it does NOT modify `brain/tick.py` or
> any non-`brain/llm/client.py` / non-`brain/ui/llm_runtime.py` /
> non-`brain/ui/__main__.py` source file; it does NOT change the
> default offline behavior of any existing REQUIRED or STRUCTURAL
> fixture.
```

The existing v0.19 banner remains in place beneath the new one
(per the existing banner-history convention in the catalog).

---

## 6. `tools/catalog.py` EXPECTED_COUNTS update

Current dict (`tools/catalog.py:27-40`):

```python
# v0.19 expected counts — bumped by the Phase 3.10c Autosave Policy
# catalog patch (I-AUTOSAVE-01..15: +11 REQUIRED, +3 STRUCTURAL,
# +1 OBSERVED) plus the Phase 3.9 I-PERSIST-16 reclassification
# (NOT-EXERCISED -> STRUCTURAL; row ID and position preserved;
# proposition narrowed to "brain/ui/persistence.py owns no autosave
# trigger or background autosave hook"): net +11 REQUIRED, +4
# STRUCTURAL, +1 OBSERVED, -1 NOT-EXERCISED.
EXPECTED_COUNTS: dict[str, int] = {
    "REQUIRED": 212,
    "STRUCTURAL": 83,
    "NOT-EXERCISED": 9,
    "DEFERRED": 12,
    "OBSERVED": 15,
}
```

Replacement (Step 8 writes this verbatim):

```python
# v0.20 expected counts — bumped by the Phase 3.11 Codex CLI Runtime
# Option catalog patch (I-LLMTOG-16/17/18: +2 REQUIRED, +1 OBSERVED;
# I-LLMTOG-12 row body updates in place from four-member to
# five-member assertion). The Phase 3.8b I-LLMTOG-* family is
# extended additively; no Phase 3.8b row is retired or renamed.
EXPECTED_COUNTS: dict[str, int] = {
    "REQUIRED": 214,
    "STRUCTURAL": 83,
    "NOT-EXERCISED": 9,
    "DEFERRED": 12,
    "OBSERVED": 16,
}
```

The banner comment is the only place the v0.19 numbers appear in
`tools/catalog.py`; the gate check at runtime uses
`EXPECTED_COUNTS` only.

---

## 7. `brain/_catalog_ids.py` entries

The generator command `python3 -m tools.catalog generate-ids`
produces `brain/_catalog_ids.py` from the parsed catalog. The
Step 8 patch runs this command after editing the catalog and
commits the regenerated file. The new entries (added in
alphabetical-then-numeric order inside the I-LLMTOG block):

```python
I_LLMTOG_16 = "I-LLMTOG-16"
I_LLMTOG_17 = "I-LLMTOG-17"
I_LLMTOG_18 = "I-LLMTOG-18"
```

These IDs are referenced by:

```text
brain/ui/fixtures/llm_runtime_codex_cli_requires_executable.py
  (Step 9; cites I_LLMTOG_16 in its ROW_ID constant)
brain/ui/fixtures/llm_runtime_codex_cli_factory.py
  (Step 9; cites I_LLMTOG_17 in its ROW_ID constant)
```

I-LLMTOG-18 has no fixture file; the OBSERVED row body documents
the smoke procedure.

---

## 8. `brain/invariants.py` FIXTURE_MODULES update

The `FIXTURE_MODULES` list at `brain/invariants.py` enumerates
every fixture module that the runner discovers. Step 9 adds:

```python
"brain.ui.fixtures.llm_runtime_codex_cli_requires_executable",
"brain.ui.fixtures.llm_runtime_codex_cli_factory",
```

Insertion order: alphabetical within the `llm_runtime_*` block.
Both new entries land after
`brain.ui.fixtures.llm_runtime_claude_cli_requires_executable`
and before any non-`llm_runtime_` module.

The total fixture count rises from 130 to 132. The catalog
fixture mapping table (INVARIANT_CATALOG.md lines 827-838) gains
two new rows:

```text
| `brain/ui/fixtures/llm_runtime_codex_cli_requires_executable.py` | I-LLMTOG-16 |
| `brain/ui/fixtures/llm_runtime_codex_cli_factory.py`              | I-LLMTOG-17 |
```

A `_PHASE3_11_PENDING_ROWS` block MAY be added at the top of
`brain/invariants.py` (matching the documentary pattern used by
prior phases) to record that I-LLMTOG-16/17 are pending until
Step 9 lands the fixtures; the block is drained in Step 9 when
both modules are present and the runner reports them green. The
plan's default position is to add the block in Step 8 and drain
it in Step 9; the corrigenda did not lock either way, so Step 8
may also skip the block if the patch is small enough to land
fixtures and rows together.

---

## 9. Step 8 file budget (catalog patch)

The Step 8 catalog patch edits exactly these files:

```text
INVARIANT_CATALOG.md         add I-LLMTOG-16/17/18 rows after
                             I-LLMTOG-15 in the existing table;
                             update I-LLMTOG-12 body per Section 4;
                             add the v0.20 banner per Section 5;
                             add the two new fixture rows per
                             Section 8.
tools/catalog.py             replace EXPECTED_COUNTS dict and
                             the leading banner comment per
                             Section 6.
brain/_catalog_ids.py        regenerated via
                             `python3 -m tools.catalog generate-ids`
                             after the catalog edit.
brain/invariants.py          (optional) add _PHASE3_11_PENDING_ROWS
                             block per Section 8; do not add
                             FIXTURE_MODULES entries yet (those
                             land in Step 9 when the modules
                             exist).
README.md                    add v0.20 changelog entry under the
                             existing version-banner list; do not
                             touch other sections.
CURRENT_MISSION.md           update baseline counts (REQUIRED 214,
                             OBSERVED 16) and bump "Catalog: v0.20".
CURRENT_CAMPAIGN.md          update baseline counts (REQUIRED 214,
                             OBSERVED 16) and bump "Catalog: v0.20".
```

Excluded from Step 8:

```text
brain/ui/llm_runtime.py      runtime changes belong to Step 9.
brain/llm/client.py          new class belongs to Step 9.
brain/ui/__main__.py         CLI flag belongs to Step 9.
brain/ui/fixtures/*.py       new and extended fixtures belong
                             to Step 9.
brain/tlica/                 untouched.
lean_reference/              untouched.
brain/tick.py                untouched.
brain/ui/persistence*.py     untouched.
brain/ui/autosave.py         untouched.
brain/ui/session.py          untouched.
```

Step 8 validation (the patch commit body MUST include these):

```bash
python3 -m tools.catalog counts        # expect 214/83/9/12/16
python3 -m tools.citations verify      # 102 citations resolve
                                       # (was 100; +1 for
                                       #  I-LLMTOG-16, +1 for
                                       #  I-LLMTOG-17; OBSERVED
                                       #  I-LLMTOG-18 does not
                                       #  carry a Lean citation)
python3 -m tools.import_audit          # agency.py clean
bash tools/check_all.sh                # 213/83/7-OBS GREEN
                                       # (the runner still sees
                                       # 213 REQUIRED GREEN
                                       # because the new fixtures
                                       # have not landed; the
                                       # _PHASE3_11_PENDING_ROWS
                                       # block, if added,
                                       # documents that
                                       # I-LLMTOG-16/17 are
                                       # PENDING until Step 9.
                                       # The catalog gate still
                                       # passes because the
                                       # EXPECTED_COUNTS reflect
                                       # the catalog rows, not
                                       # the fixture coverage.)
```

The Step 8 commit is INTENTIONALLY a documentation-only catalog
edit. The runner does not turn red because the pending rows are
recorded in the pending block (and/or in a "pending I-LLMTOG-16
and I-LLMTOG-17 land in Step 9" docstring comment).

If the corrigenda or the reviewer prefers a single combined
Step 8+9 commit (catalog + fixtures in one shot), the plan
accepts that variation; the validation surface is the same with
fully-green REQUIRED 215 after the runner discovers the new
fixtures. The default plan keeps Step 8 and Step 9 separate to
minimize the diff per commit.

---

## 10. Step 9 file budget (runtime implementation) — recap

For completeness (Step 9 is not part of THIS patch but inherits
the plan):

```text
brain/ui/llm_runtime.py        add CODEX_CLI enum member;
                               add codex_cli_executable: str field;
                               add _build_codex_cli_client helper;
                               extend factory dispatch;
                               extend _ACCEPTED_MODE_VALUES;
                               extend parse_llm_runtime_args to
                               accept --llm-mode codex-cli and
                               BRAIN_LLM_MODE=codex-cli; bind
                               --llm-codex-cli-executable to
                               LlmRuntimeConfig.codex_cli_executable.
brain/llm/client.py            add CodexCLIClient dataclass with
                               __post_init__ (_which check) and
                               eval_consistency (subprocess.run
                               with bounded timeout and stderr).
brain/ui/__main__.py           add --llm-codex-cli-executable
                               argparse argument; update
                               --llm-mode help text to include
                               codex-cli.
brain/ui/fixtures/
  llm_runtime_codex_cli_requires_executable.py   NEW
  llm_runtime_codex_cli_factory.py                NEW
  llm_runtime_mode_closed.py                      EXTEND
  llm_runtime_factory_per_mode.py                 EXTEND
  llm_runtime_explicit_opt_in.py                  EXTEND
  llm_runtime_cache_gated.py                      EXTEND
  llm_runtime_tick_seam.py                        EXTEND
  llm_runtime_print_once_independent.py           EXTEND
  llm_runtime_config_frozen.py                    EXTEND
  llm_runtime_static_audit.py                     EXTEND
brain/invariants.py            FIXTURE_MODULES += two new entries;
                               drain _PHASE3_11_PENDING_ROWS
                               (if added in Step 8).
README.md                      brief docs section for
                               --llm-mode codex-cli.
```

Step 9 validation:

```bash
python3 -m tools.catalog counts        # 214/83/9/12/16 still ok
python3 -m tools.citations verify      # 102 citations still resolve
python3 -m tools.import_audit          # agency.py clean
python3 -m brain.invariants run        # 305 rows / 215 REQUIRED GREEN /
                                       # 83 STRUCTURAL GREEN /
                                       # 8 OBSERVED pass /
                                       # 0 gate failures
bash tools/check_all.sh                # All checks passed.
```

(The REQUIRED green count rises from 213 to 215: +1 for
I-LLMTOG-16 fixture, +1 for I-LLMTOG-17 fixture. STRUCTURAL stays
at 83. OBSERVED pass count rises by 1 only if I-LLMTOG-18 is
implemented as a runner-visible OBSERVED entry; per the
corrigenda Section 11, I-LLMTOG-18 has no fixture file, so the
runner's OBSERVED pass count remains 7. The catalog gate sees 16
OBSERVED rows total; the runner sees 7 of them as
runner-visible.)

---

## 11. Lean citation discipline

The new REQUIRED rows are engineering hypotheses, not Lean
theorem claims (mirroring the entire I-LLMTOG-* family). The
citation file `tools/citations.py` reads citations from the
catalog's `Source` column when the row's source kind is
`LEAN`. For engineering-hypothesis rows the citation verifier
does NOT require a Lean citation.

```text
I-LLMTOG-16   ENGINEERING_HYPOTHESIS   no Lean citation
I-LLMTOG-17   ENGINEERING_HYPOTHESIS   no Lean citation
I-LLMTOG-18   OBSERVED                  no Lean citation
```

Citation count after Step 8 patch: unchanged at 100 if the row
bodies above are written verbatim (the catalog's citation
extractor reads Lean citations from row bodies; the engineering-
hypothesis source kind disables that requirement). If the row
bodies inadvertently include `Lean ...` references, the
citation verifier would count them; the plan's default position
is to keep the row bodies citation-free (matching Phase 3.8b).

If the Step 8 validation reports a citation count > 100, the
plan's default position is to investigate before merging. The
plan does NOT pre-authorize a citation count of 102; that was a
contingency note in Section 9.

---

## 12. I-LLMTOG-15 disposition

I-LLMTOG-15 (NOT-EXERCISED, "no LLM runtime save / export path")
applies to the entire LLM runtime surface. Adding `codex-cli`
does not introduce a new save / export path; the cache directory
remains shared across all model-backed modes. I-LLMTOG-15
remains UNCHANGED in row body, ID, status, source, module, and
fixture binding.

The CODEX_CLI factory does NOT write to disk. The CachedClient
wrapping path is shared with claude-cli and anthropic-api;
adding codex-cli does NOT create a new persistent path.

---

## 13. Rejected alternatives (for the reviewer)

```text
A. Open a new I-CODEXCLI-* family
   Rejected: Section 12 of the corrigenda. Cross-mode rows
   already audit the closed enum and factory dispatch. A new
   family would duplicate them per-mode.

B. Add a STRUCTURAL row for the new CodexCLIClient class
   Rejected: I-LLMTOG-13 (static AST audit, STRUCTURAL) and
   I-LLMTOG-11 (config_frozen, STRUCTURAL) cover the new class
   shape transitively when their fixtures extend to the new
   module.

C. Add a NOT-EXERCISED placeholder for codex-cli streaming /
   tool-use / multimodal
   Rejected: synthesis Section 8.4; LLMClient protocol has
   exactly one method (eval_consistency). Streaming/tool-use/
   multimodal are out of scope for Phase 3.11 and would not
   inform the live behavior test.

D. Add a DEFERRED row for codex-specific timeout
   Rejected: corrigenda Section 5; timeout_seconds is shared.

E. Add a DEFERRED row for codex-specific env var auto-pickup
   Rejected: corrigenda Section 8; environment-only auto-
   selection is forbidden by I-LLMTOG-04.

F. Add an extra OBSERVED row for the --print-once + codex-cli
   smoke
   Rejected: I-LLMTOG-10 already audits --print-once
   independence across modes; the cross-mode fixture extends.

G. Combine Step 8 catalog patch and Step 9 implementation into
   one commit
   Accepted as a permitted variation in Section 9; the plan's
   default keeps them separate for diff clarity. Either is
   reviewable.
```

---

## 14. Stop point

This document is the canonical binding for the Step 8 catalog
patch and the Step 9 implementation. The next stopping point is:

```text
Step 7 — Review gate A — Codex CLI

  Stop unless Step 6 is explicitly accepted.
```

No further work is authorized until the user explicitly accepts
this plan. The campaign must NOT:

```text
- proceed to Step 8 (apply the catalog patch)
- proceed to Step 9 (implement the runtime)
- proceed to Step 10 (live test kickoff)
- proceed to any later step
```

without an explicit user acceptance of this Step 6 plan at the
Step 7 review gate A.

The final report at the end of this campaign run will record
the Step 7 stop point and surface this document for review.
