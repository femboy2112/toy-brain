# PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md

## Purpose

Execute `CURRENT_CAMPAIGN.md` Step 16: DB observability and backup
behavior tests for the Phase 3.11 comprehensive live behavior campaign.

Source: CURRENT_CAMPAIGN.md Step 16

Required artifact:

```text
PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
```

This is a report-only step. It records actual behavior and does not edit
runtime code, fixtures, catalog rows, mission/campaign routing prose, or
prior phase audits.

## Baseline

```text
Branch: campaign/comprehensive-live-behavior-test
Catalog: v0.20
Counts: 214 REQUIRED / 83 STRUCTURAL / 9 NOT-EXERCISED / 12 DEFERRED / 16 OBSERVED
Step before execution: Step 16
Prior step evidence: fd8027a phase3.11 step15: autosave behavior report
Required Step 16 report before execution: absent
```

Preflight:

```text
python3 -m tools.catalog counts       PASS
brain_campaign_state                  READY: Step 16
git status --short --branch           clean on campaign branch
```

## Test Method

Temporary helper:

```text
/tmp/phase3_11_db_step16/run_db_observations.py
```

Helper policy:

```text
deterministic local Python stdlib helper
no network
no real LLM calls
no repo writes
SQLite files only under /tmp/phase3_11_db_*
temporary DB directory removed after successful observation run
```

Primary scripted state setup:

```text
temporary DB: /tmp/phase3_11_db_pjga30d5/session.sqlite3
client: OfflineStandInClient
commands:
  /session-status
  /stream phase3 step16 db observation payload
  /stream-promote promo-strm-chunk-1
  /step
  /save-session
```

The setup saved a real session DB with one stream chunk, one stream
candidate, and `tick=1`.

## Observation Table

| ID | Type | Automation | Observation | Verdict |
| --- | --- | --- | --- | --- |
| 16.db-status.1 | SST | yes | In-process `/db-status` returned `db-status: schema=v1 catalog='v0.17' bytes=73728` for the configured saved session DB. | works |
| 16.db-status.2 | SST | yes | `python3 -m brain.ui --session-db ... --db-status` exited 0 and printed an `ok` one-line status with path, `exists=True`, schema, catalog, and bytes. | works |
| 16.db-verify.1 | SST | yes | In-process `/db-verify` returned `db-verify PASS: schema=v1 chunks=1 candidates=1` without activating or replacing the live session. | works |
| 16.db-verify.2 | SST | yes | `python3 -m brain.ui --session-db ... --db-verify` exited 0 and printed `db-verify = pass` with schema, chunks, candidates, and empty error text. | works |
| 16.db-summary.1 | SST | yes | `/db-summary` returned bounded row counts: `profile=3 msi=3/thr=1/2 ptcns=3 registry=2 chunks=1 candidates=1`. | works |
| 16.profile-summary.1 | SST | yes | `/profile-summary` returned `profile-summary: rows=3 (complete)`. | works |
| 16.stream-db-summary.1 | SST | yes | `/stream-db-summary` returned `stream-db-summary: chunks=1 candidates=1 head=1 tail=1`. | works |
| 16.db-diff.1 | SST | yes | `/db-diff` returned `db-diff: matches (diff_count=0)`. | works |
| 16.db-backup.1 | SST | yes | In-process `/db-backup .../session.sqlite3.bak` returned `db-backup ok` with `pages=18/18 bytes=73728`; the source DB hash was unchanged after backup. The backup DB hash differed from the source DB hash, so the live behavior is SQLite-API logical backup rather than byte-identical file cloning. | awkward |
| 16.db-backup.2 | SST | yes | `python3 -m brain.ui --session-db ... --db-backup .../session-force.sqlite3.bak` exited 0 and created a backup with `pages=18/18 bytes=73728`. | works |
| 16.db-backup-force.1 | SST | yes | Repeating `--db-backup` to an existing destination without `--db-backup-force` exited 1 and printed a bounded refusal naming the existing destination and `force=True` requirement. | works |
| 16.db-backup-force.2 | SST | yes | Repeating with `--db-backup-force` exited 0 and printed `overwritten=True`. | works |
| 16.db-backup-uri.1 | SST | yes | `/db-backup file:/tmp/disallowed.db` was rejected at parse time with `/db-backup destination uses forbidden URI scheme 'file'`; because parsing failed, the previous status message remained visible. | works |
| 16.ux-db.1 | MOT | env | DB status, verify, summary, diff, and backup outputs are bounded and easy to scan. The only awkward point is that the matrix phrase "byte-faithful" overstates what the SQLite backup API appears to guarantee at the file-hash level. | awkward |

## Raw Evidence Summary

### Setup

```text
/session-status:
  session-status: tick=0 queue=0 view=state chunks=0 candidates=0 db=configured

/stream phase3 step16 db observation payload:
  stream chunk 'strm-chunk-1' appended (history size = 1)

/stream-promote promo-strm-chunk-1:
  promoted stream candidate 'promo-strm-chunk-1' (queue size = 1)

/step:
  tick 1 ok (MODE_C)

/save-session:
  saved session to /tmp/phase3_11_db_pjga30d5/session.sqlite3 (chunks=1, candidates=1)

saved DB:
  bytes=73728
  sha256=6041b8e509c150d38fd118433ebdc2b2c6c3b3993ebb5c0556b94d7ba88087d8
```

### Status And Verify

```text
/db-status:
  db-status: schema=v1 catalog='v0.17' bytes=73728

python3 -m brain.ui --session-db ... --db-status:
  exit=0
  brain.ui: db-status = ok (... exists=True; schema=v1; catalog='v0.17'; bytes=73728)

/db-verify:
  db-verify PASS: schema=v1 chunks=1 candidates=1

python3 -m brain.ui --session-db ... --db-verify:
  exit=0
  brain.ui: db-verify = pass (... schema=v1; chunks=1; candidates=1; error='')
```

### Summaries And Diff

```text
/db-summary:
  db-summary: profile=3 msi=3/thr=1/2 ptcns=3 registry=2 chunks=1 candidates=1

/profile-summary:
  profile-summary: rows=3 (complete)

/stream-db-summary:
  stream-db-summary: chunks=1 candidates=1 head=1 tail=1

/db-diff:
  db-diff: matches (diff_count=0)
```

### Backup

```text
/db-backup /tmp/.../session.sqlite3.bak:
  db-backup ok: dest='/tmp/.../session.sqlite3.bak' pages=18/18 bytes=73728
  source_hash_after=6041b8e509c150d38fd118433ebdc2b2c6c3b3993ebb5c0556b94d7ba88087d8
  backup_hash=71f56764ea49b99680e42fa3ba1d8535c71cb489a093f8b8faedcc2305e1d31e

source hash before all backups:
  6041b8e509c150d38fd118433ebdc2b2c6c3b3993ebb5c0556b94d7ba88087d8
source hash after all backups:
  6041b8e509c150d38fd118433ebdc2b2c6c3b3993ebb5c0556b94d7ba88087d8
```

The backup operation preserves the source DB exactly under hash, but the
backup file itself is not byte-identical to the source file in this
observation. The operational behavior still appears correct for a
SQLite backup API copy; the wording "byte-faithful" in the Step 16
matrix should be treated as a finding for Step 18/19.

### Backup Failure Paths

```text
repeat --db-backup without force:
  exit=1
  db-backup = fail (... error='dest_path ... exists; pass force=True to overwrite')

repeat --db-backup with --db-backup-force:
  exit=0
  db-backup = ok (... overwritten=True; error='')

/db-backup file:/tmp/disallowed.db:
  parse_error=/db-backup destination uses forbidden URI scheme 'file'
```

## Findings

- DB status, verify, summary, profile summary, stream summary, and diff
  all execute successfully against a real saved session DB.
- One-shot `--db-status`, `--db-verify`, and `--db-backup` short-circuit
  commands work without curses launch.
- `/db-backup` and `--db-backup` preserve the source DB bytes.
- Backup destination overwrite protection works by default and explicit
  force works.
- URI-scheme backup destinations are rejected before SQLite opens them.
- The matrix wording "byte-faithful SQLite backup" is awkward: observed
  backup DB files had the same size but different hash from the source,
  while the source stayed unchanged and the operation reported page-copy
  success.

No Step 16 observation produced a gating failure. No behavior was
patched.

## Validation

Post-report validation:

```text
python3 -m tools.catalog counts       PASS
python3 -m tools.citations verify     PASS (100 citations)
python3 -m tools.import_audit         PASS
python3 -m brain.invariants run       PASS (305 rows checked; gate failures: 0)
bash tools/check_all.sh               PASS (All checks passed)
```

Scope guard after validation:

```text
git status --short                    only PHASE3_11_DB_OBSERVABILITY_BEHAVIOR_REPORT.md
git diff --name-only                  no tracked source/catalog/mission diff
temporary DB/helper state             DB temp dir removed; helper remains only under /tmp
```

## Next

The next campaign step after this report is Step 17:

```text
PHASE3_11_LLM_RUNTIME_BEHAVIOR_REPORT.md
```
