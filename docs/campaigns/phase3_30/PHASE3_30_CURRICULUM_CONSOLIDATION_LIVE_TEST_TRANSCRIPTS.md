# Phase 3.30 — Curriculum Consolidation Live Test Transcripts

This file captures the raw deterministic outputs of the Phase 3.30
curriculum consolidation runner on the v1 ten-trial battery. Every
line below is reproducible bit-identically by re-running:

```bash
python3 -m brain.development.curriculum_consolidation_probe
```

## Runner output (table form)

```text
curriculum_consolidation_live_test version=phase3.30.v1 trials=10 pass=10 warn=0 fail=0 na=0 fp=0 fn=0 survived=23 decayed=3 rejected=3 reuse=1
  T01_single_printable           pass   cond=single_structure               survived=1 decayed=0 rejected=0 reuse=False
  T02_single_singleton           pass   cond=single_structure               survived=0 decayed=0 rejected=1 reuse=False
  T03_seq_distinct_2             pass   cond=sequential_noninterfering      survived=2 decayed=0 rejected=0 reuse=False
  T04_seq_distinct_3             pass   cond=sequential_noninterfering      survived=3 decayed=0 rejected=0 reuse=False
  T05_collision_pair             pass   cond=sequential_interfering         survived=1 decayed=0 rejected=1 reuse=False
  T06_collision_in_3             pass   cond=sequential_interfering         survived=2 decayed=0 rejected=1 reuse=False
  T07_decay_overflow_5           pass   cond=decay_on_disuse                survived=4 decayed=1 rejected=0 reuse=False
  T08_decay_overflow_6           pass   cond=decay_on_disuse                survived=4 decayed=2 rejected=0 reuse=False
  T09_reuse_oldest               pass   cond=reuse_after_newer              survived=3 decayed=0 rejected=0 reuse=True
  T10_reuse_negative             pass   cond=reuse_after_newer              survived=3 decayed=0 rejected=0 reuse=False
  digest=9412acec1163b978
real_model_calls=0 cache_writes=0 forbidden_term_hits=0
```

## Per-trial digest fingerprints

| trial_id                  | learning_evidence_digest | reasoning_trace_digest |
|---|---|---|
| T01_single_printable      | 79a4987828586a40         | 0000000000000000       |
| T02_single_singleton      | 961f5b62dc28840f         | 0000000000000000       |
| T03_seq_distinct_2        | 2c26e0f0b7d5dda8         | 0000000000000000       |
| T04_seq_distinct_3        | df13e179363239e8         | 0000000000000000       |
| T05_collision_pair        | 6a2c8ab554f3186c         | 0000000000000000       |
| T06_collision_in_3        | 73d95527ed773054         | 0000000000000000       |
| T07_decay_overflow_5      | 07b1a65c07e1e8f4         | 0000000000000000       |
| T08_decay_overflow_6      | b59c5bde1bac71f7         | 0000000000000000       |
| T09_reuse_oldest          | 708d907000f20fbb         | 8c8a5313841a3921       |
| T10_reuse_negative        | cab996ff1ea9e2ee         | cda017231667843f       |

Zero-digest reasoning entries reflect trials whose only steps are
exposures (the curriculum's exposure path is admission-only and
emits no probe-step reasoning trace). T09 and T10 carry non-zero
reasoning digests because they run a final probe through
`run_agent_interaction_step`.

## Per-trial dispatch trace digest tuples

| trial_id                  | dispatch_trace_digests |
|---|---|
| T01_single_printable      | (6e14986140a6cce2,) |
| T02_single_singleton      | (6e14986140a6cce2,) |
| T03_seq_distinct_2        | (6e14986140a6cce2, 3e96346dc48a7d8f) |
| T04_seq_distinct_3        | (6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295) |
| T05_collision_pair        | (6e14986140a6cce2, 9cacc9d7e8354f67) |
| T06_collision_in_3        | (6e14986140a6cce2, 3e96346dc48a7d8f, bb88e1db23a912b4) |
| T07_decay_overflow_5      | (6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295, 21e67f326c33cd9d, eb02cd03044208b3) |
| T08_decay_overflow_6      | (6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295, 21e67f326c33cd9d, eb02cd03044208b3, 4e9cc46300295d5d) |
| T09_reuse_oldest          | (6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295, 5e2e66d5a47349fb) |
| T10_reuse_negative        | (6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295, 21e67f326c33cd9d) |

## Per-trial audit trail

### T01_single_printable
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  SURVIVED
```

### T02_single_singleton
```
R01_8b0635ab  digest=8b0635ab66676036  admitted=0  last_access=0  REJECTED  (classification=singleton)
```

### T03_seq_distinct_2
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  SURVIVED
S02_a996ad3d  digest=a996ad3d8bdc5e3b  admitted=1  last_access=1  SURVIVED
```

### T04_seq_distinct_3
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  SURVIVED
S02_a996ad3d  digest=a996ad3d8bdc5e3b  admitted=1  last_access=1  SURVIVED
S03_9bb2ad07  digest=9bb2ad079f553a05  admitted=2  last_access=2  SURVIVED
```

### T05_collision_pair
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  SURVIVED
R02_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  REJECTED  (collision with S01)
```

### T06_collision_in_3
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  SURVIVED
S02_a996ad3d  digest=a996ad3d8bdc5e3b  admitted=1  last_access=1  SURVIVED
R03_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  REJECTED  (collision with S01)
```

### T07_decay_overflow_5
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  DECAYED   (LRU evicted by step 4 admission)
S02_a996ad3d  digest=a996ad3d8bdc5e3b  admitted=1  last_access=1  SURVIVED
S03_9bb2ad07  digest=9bb2ad079f553a05  admitted=2  last_access=2  SURVIVED
S04_e8cfe826  digest=e8cfe826475e7d96  admitted=3  last_access=3  SURVIVED
S05_9dfde01c  digest=9dfde01c9a4cfc38  admitted=4  last_access=4  SURVIVED
```

### T08_decay_overflow_6
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  DECAYED   (evicted by step 4)
S02_a996ad3d  digest=a996ad3d8bdc5e3b  admitted=1  last_access=1  DECAYED   (evicted by step 5)
S03_9bb2ad07  digest=9bb2ad079f553a05  admitted=2  last_access=2  SURVIVED
S04_e8cfe826  digest=e8cfe826475e7d96  admitted=3  last_access=3  SURVIVED
S05_9dfde01c  digest=9dfde01c9a4cfc38  admitted=4  last_access=4  SURVIVED
S06_81e8ce9b  digest=81e8ce9bc640c0b0  admitted=5  last_access=5  SURVIVED
```

### T09_reuse_oldest
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=3  SURVIVED  (bumped by probe at step 3)
S02_a996ad3d  digest=a996ad3d8bdc5e3b  admitted=1  last_access=1  SURVIVED
S03_9bb2ad07  digest=9bb2ad079f553a05  admitted=2  last_access=2  SURVIVED
probe: input='alpha beta' digest=457c99dd93973d27 reuse_observed=True reused_id='S01_457c99dd'
```

### T10_reuse_negative
```
S01_457c99dd  digest=457c99dd93973d27  admitted=0  last_access=0  SURVIVED
S02_a996ad3d  digest=a996ad3d8bdc5e3b  admitted=1  last_access=1  SURVIVED
S03_9bb2ad07  digest=9bb2ad079f553a05  admitted=2  last_access=2  SURVIVED
probe: input='eta eta theta' digest=e8cfe826475e7d96 reuse_observed=False reused_id=''
```

## Determinism check

Two consecutive invocations of
`run_curriculum_consolidation_live_test()` produce identical
`digest_hex16` (`9412acec1163b978`) and bit-identical `trials`
tuples. Verified by I-CURR-11 fixture in
`brain/ui/fixtures/curriculum_learning_reasoning_dispatch.py`.

## Resource accounting

```
real_model_calls         = 0
cache_writes             = 0
forbidden_term_hits      = 0
determinism_failures     = 0
invariant_failures       = 0
gate_runner gates passed = 5 / 5
```
