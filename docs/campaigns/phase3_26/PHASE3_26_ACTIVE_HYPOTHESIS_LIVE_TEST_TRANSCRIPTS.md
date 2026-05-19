# Phase 3.26 — Active Hypothesis + Self-Directed Probe Loop — Live Test Transcripts

Deterministic captured output of one fresh run of
`python3 -m brain.development.active_hypothesis_probe` plus the
canonical serialized form used by the I-AHYP-12 report digest. All
content is bounded printable. No forbidden non-claim term appears in
any line.

## 1. `python3 -m brain.development.active_hypothesis_probe`

```text
active_hypothesis_live_test version=phase3.26.v1 trials=10 pass=10 warn=0 fail=0 na=0 fp=0 fn=0 winners=3 no_survivor=3 cache_reuse=2
  T01_control_empty              pass   cond=control_no_ambiguity           survivors=0 winner=<none>                           cache_hit=False
  T02_control_singleton          pass   cond=control_no_ambiguity           survivors=0 winner=<none>                           cache_hit=False
  T03_single_aba                 pass   cond=single_hypothesis_converges    survivors=1 winner=H_RENAME_S_ABA                   cache_hit=False
  T04_single_abb                 pass   cond=single_hypothesis_converges    survivors=1 winner=H_RENAME_S_ABB                   cache_hit=False
  T05_multi_abc                  pass   cond=multi_hypothesis_narrows       survivors=3 winner=<none>                           cache_hit=False
  T06_multi_abab                 pass   cond=multi_hypothesis_narrows       survivors=3 winner=<none>                           cache_hit=False
  T07_nosurv_aa                  pass   cond=no_hypothesis_survives         survivors=0 winner=<none>                           cache_hit=False
  T08_nosurv_aab                 pass   cond=no_hypothesis_survives         survivors=0 winner=<none>                           cache_hit=False
  T09_reuse_aba                  pass   cond=reuse_cached_hypothesis        survivors=1 winner=H_RENAME_S_ABA                   cache_hit=True
  T10_reuse_aa                   pass   cond=reuse_cached_hypothesis        survivors=0 winner=<none>                           cache_hit=True
  digest=86b67d97daeb251d
real_model_calls=0 cache_writes=0 forbidden_term_hits=0
```

Exit code: `0` (no FAIL, no WARN).

## 2. Canonical serialized form (used by `active_hypothesis_live_test_digest`)

Each block is `_serialize_result(r)` for the corresponding trial.
The bytes joined by `"\n"` and SHA-256'd give the report digest
`86b67d97daeb251d`.

### T01_control_empty

```text
T01_control_empty
control_no_ambiguity
pass
23a5277924c828fe
survivors=0
winner=
no_survivor=False
cache_hit=False
probe_count2=0
fp=False
fn=False
e3b0c44298fc1c14
0000000000000000

active_hypothesis_trial id=T01_control_empty cond=control_no_ambiguity candidates=0 survivors=0 winner=<none> no_survivor=False cache_hit=False verdict=pass
```

### T02_control_singleton

```text
T02_control_singleton
control_no_ambiguity
pass
8b0635ab66676036
survivors=0
winner=
no_survivor=False
cache_hit=False
probe_count2=0
fp=False
fn=False
e3b0c44298fc1c14
0000000000000000

active_hypothesis_trial id=T02_control_singleton cond=control_no_ambiguity candidates=0 survivors=0 winner=<none> no_survivor=False cache_hit=False verdict=pass
```

### T03_single_aba

```text
T03_single_aba
single_hypothesis_converges
pass
9dfde01c9a4cfc38
survivors=1
winner=H_RENAME_S_ABA
no_survivor=False
cache_hit=False
probe_count2=0
fp=False
fn=False
78dcacc166a019a2
fe28044a8803dd2c
6e14986140a6cce2|9cacc9d7e8354f67|c2ceb0cc0489da30|d374ce299c8694a1
active_hypothesis_trial id=T03_single_aba cond=single_hypothesis_converges candidates=4 survivors=1 winner=H_RENAME_S_ABA no_survivor=False cache_hit=False verdict=pass
cand|H_RENAME_S_ABA|S_ABA|9dfde01c9a4cfc38|rename_only|selected
cand|H_RENAME_S_ABB|S_ABB|81e8ce9bc640c0b0|rename_only|falsified
cand|H_APPEND_POS0_S_ABCA|S_ABCA|ddca804b34373e00|append_pos0_token|falsified
cand|H_APPEND_NEW_S_ABCD|S_ABCD|4fe018cac6762a9d|append_new_token|falsified
probe|H_RENAME_S_ABA|9dfde01c9a4cfc38|A B A|partial-recurring|confirmed|agent-input:00001|6e14986140a6cce2|e0fff2a645f21265
probe|H_RENAME_S_ABB|9dfde01c9a4cfc38|A B A|partial-recurring|falsified|agent-input:00002|9cacc9d7e8354f67|f96154794ec8ae48
probe|H_APPEND_POS0_S_ABCA|d1e31f8693d6e3ca|A B A A|partial-recurring|falsified|agent-input:00003|c2ceb0cc0489da30|7c81120cc2aabb1f
probe|H_APPEND_NEW_S_ABCD|fa7e27d2ab882ff3|A B A C|partial-recurring|falsified|agent-input:00004|d374ce299c8694a1|fe28044a8803dd2c
```

### T04_single_abb

```text
T04_single_abb
single_hypothesis_converges
pass
81e8ce9bc640c0b0
survivors=1
winner=H_RENAME_S_ABB
no_survivor=False
cache_hit=False
probe_count2=0
fp=False
fn=False
1d472455c4593551
1872f23d1c5fae03
6e14986140a6cce2|9cacc9d7e8354f67|c2ceb0cc0489da30|d374ce299c8694a1
active_hypothesis_trial id=T04_single_abb cond=single_hypothesis_converges candidates=4 survivors=1 winner=H_RENAME_S_ABB no_survivor=False cache_hit=False verdict=pass
cand|H_RENAME_S_ABA|S_ABA|9dfde01c9a4cfc38|rename_only|falsified
cand|H_RENAME_S_ABB|S_ABB|81e8ce9bc640c0b0|rename_only|selected
cand|H_APPEND_POS0_S_ABCA|S_ABCA|ddca804b34373e00|append_pos0_token|falsified
cand|H_APPEND_NEW_S_ABCD|S_ABCD|4fe018cac6762a9d|append_new_token|falsified
probe|H_RENAME_S_ABA|81e8ce9bc640c0b0|A B B|partial-recurring|falsified|agent-input:00001|6e14986140a6cce2|69134c4f8d53075e
probe|H_RENAME_S_ABB|81e8ce9bc640c0b0|A B B|partial-recurring|confirmed|agent-input:00002|9cacc9d7e8354f67|762547fdc7e6cfea
probe|H_APPEND_POS0_S_ABCA|40057bcfaed5886a|A B B A|recurring-form|falsified|agent-input:00003|c2ceb0cc0489da30|f51390785b880458
probe|H_APPEND_NEW_S_ABCD|9a125a08f8b485f0|A B B C|partial-recurring|falsified|agent-input:00004|d374ce299c8694a1|1872f23d1c5fae03
```

### T05_multi_abc

3 survivors: `H_RENAME_S_ABC`, `H_APPEND_NEW_S_ABCD`,
`H_APPEND_POS0_S_ABCA`. All three retain `SURVIVING` status; the
runner does NOT promote any to `SELECTED`. Winner_id remains `""`.

### T06_multi_abab

3 survivors: `H_RENAME_S_ABAB`, `H_APPEND_NEW_S_ABABC`,
`H_APPEND_POS0_S_ABABA`. All three retain `SURVIVING` status;
winner_id remains `""`.

### T07_nosurv_aa

0 survivors. Every candidate of the `(repeated, 2)` bucket
(`H_RENAME_S_AB`, `H_APPEND_NEW_S_ABA`, `H_APPEND_NEW_S_ABC`,
`H_APPEND_POS0_S_ABAA`) is marked `FALSIFIED`. Winner_id is `""`;
`no_hypothesis_survives = True`. The runner does NOT invent a
winner.

### T08_nosurv_aab

0 survivors. Every candidate of the `(partial-recurring, 3)` bucket
is marked `FALSIFIED` against the input shape `A A B`. Winner_id is
`""`; `no_hypothesis_survives = True`.

### T09_reuse_aba

Cache hit on T03's input (`red blue red`). The serialized form
mirrors T03 with `cache_hit=True`, `probe_count2=0`; no new probes
are executed.

### T10_reuse_aa

Cache hit on T07's input (`red red`). The serialized form mirrors
T07 with `cache_hit=True`, `probe_count2=0`; no new probes are
executed; `no_hypothesis_survives` remains True.

## 3. A13 benchmark axis transcript (excerpt)

```text
  axis active_hypothesis -> pass
    A13.01 pass control empty: candidates=0 survivors=0 winner=''
    A13.02 pass control singleton: candidates=0 survivors=0 winner=''
    A13.03 pass single A B A: survivors=1 winner=H_RENAME_S_ABA
    A13.04 pass single A B B: survivors=1 winner=H_RENAME_S_ABB
    A13.05 pass multi A B C: survivors=3 winner=''
    A13.06 pass multi A B A B: survivors=3 winner=''
    A13.07 pass no_survivor A A: candidates=4 survivors=0 no_surv=True
    A13.08 pass no_survivor A A B: candidates=4 survivors=0
    A13.09 pass reuse A B A: cache_hit=True probe_count2=0 winner=H_RENAME_S_ABA
    A13.10 pass reuse A A: cache_hit=True probe_count2=0 no_surv=True
    A13.11 pass probe non-leak: probe_total=32 leak_ok=True
    A13.12 pass report digest stable: digest=86b67d97daeb251d match=True
    A13.13 pass active_hypothesis_probe source non-claim-clean: hit=None
    A13.14 pass A1..A12 case counts retained: got=(9, 5, 4, 5, 9, 3, 4, 7, 7, 12, 12, 14) expected=(9, 5, 4, 5, 9, 3, 4, 7, 7, 12, 12, 14)
```

## 4. Full battery summary

```text
agent-benchmark phase3.26.v1 total=105 passed=104 warned=1 failed=0
                             determinism_failures=0 real_model_calls=0
                             digest=0169f117497dba08
```

The only WARN case is the documented `A3.04` carry-over from Phase
3.21 W3 (`NOT_APPLICABLE`-overall blocker, unchanged across Phases
3.21..3.26).
