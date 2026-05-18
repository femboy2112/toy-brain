# Phase 3.25 — Osmotic Live Test Transcripts

Bounded transcript excerpts only. No raw hidden-state dumps; no
forbidden cognitive claims.

## C0 control_no_exposure (T01_control_abab)

```
operator -> cat dog cat dog
ToyI    -> [pattern_report] pattern stream_chunks=1 entries=1
           seed_id='pledger:ba9d1415920680b0' seed_recur=2 seed_sat=open
           worldlet_feedback=absent | [repl_report] repl no_command_this_step
           emit_total=0 ... | [coherence_report] coherence overall=pass
           check_total=8 | [limitation_report] limitation runtime=offline
           real_model_calls=0 cache_writes=0 substrate=bounded
           no_cognitive_claim=true | [next_action_suggestion] ...
```

Evidence digests:

```
learning_digest=581a2a881ced7f81
reasoning_digest=aad4658332c8321e
dispatch_digests=(6e14986140a6cce2,)
prior_acquired_observed=False  expected=False
transfer_observed=False        expected=False
verdict=PASS
```

## C1 true_exposure ABAB (T02_true_abab)

```
operator -> red blue red blue
ToyI    -> [pattern_report] pattern stream_chunks=1 entries=1
           seed_id='pledger:1669ab0ef2ed6bba' seed_recur=2 seed_sat=open
           worldlet_feedback=absent | ...

operator -> cat dog cat dog
ToyI    -> [pattern_report] pattern stream_chunks=2 entries=2
           seed_id='pledger:1669ab0ef2ed6bba' seed_recur=2 seed_sat=open
           worldlet_feedback=absent | ...
```

Evidence digests:

```
learning_digest=10feee0cf4a98d64
reasoning_digest=1f59da9dde68c8fd
dispatch_digests=(6e14986140a6cce2, 3e96346dc48a7d8f)
prior_acquired_observed=True   expected=True
transfer_observed=True         expected=True
verdict=PASS
```

## C1 true_exposure ABBA (T03_true_abba)

```
operator -> copper tin tin copper
ToyI    -> [pattern_report] ... seed_sat=open worldlet_feedback=absent | ...
operator -> moon sun sun moon
ToyI    -> [pattern_report] ... seed_sat=open worldlet_feedback=absent | ...
prior_acquired_observed=True   transfer_observed=True   verdict=PASS
probe_digest=40057bcfaed5886a  shape='A B B A'
```

## C1 true_exposure ABCABC (T04_true_abcabc)

```
operator -> red blue green red blue green
operator -> cat dog bird cat dog bird
prior_acquired_observed=True   transfer_observed=True   verdict=PASS
probe_digest=9cd0ca7a79c87064  shape='A B C A B C'
```

## C2 sham_exposure (T05_sham_abba_for_abab)

```
operator -> red blue blue red          # exposure digest=40057bcfaed5886a
operator -> cat dog cat dog            # probe digest=d37efc29b0c680ba (target)

prior_acquired_observed=False  expected=False
transfer_observed=False        expected=False
false_positive=False
verdict=PASS
```

Evidence digests:

```
learning_digest=b4e006d8652254e6
reasoning_digest=345c16d2c989256e
dispatch_digests=(6e14986140a6cce2, 3e96346dc48a7d8f)
```

## C3 distractor_interference (T06_distractor_abab)

```
operator -> red blue red blue         # target  digest=d37efc29b0c680ba
operator -> kettle pot kettle pot     # distractor digest != target
operator -> moss fern moss fern       # distractor digest != target
operator -> cat dog cat dog           # probe   digest=d37efc29b0c680ba

prior_acquired_observed=True   transfer_observed=True   verdict=PASS
```

Evidence digests:

```
learning_digest=6aca915eb56c6d69
reasoning_digest=0ecb4d351a81c66c
dispatch_digests=(6e14986140a6cce2, 3e96346dc48a7d8f, 0d25a6d18ddff295, 21e67f326c33cd9d)
```

## C1 delayed (T07_delayed_abab)

```
operator -> red blue red blue          # target
operator -> kettle pot                  # unrelated bounded input
operator -> moss fern                   # unrelated bounded input
operator -> cat dog cat dog             # probe

prior_acquired_observed=True   transfer_observed=True   verdict=PASS
```

## C0 control AAB (T08_control_aab)

```
operator -> cat cat dog                 # probe digest=e8cfe826475e7d96 (target)

prior_acquired_observed=False  transfer_observed=False  verdict=PASS
```

## C1 renamed AAB (T09_renamed_aab)

```
operator -> red red blue                # exposure digest=e8cfe826475e7d96
operator -> cat cat dog                 # probe   digest=e8cfe826475e7d96

prior_acquired_observed=True   transfer_observed=True   verdict=PASS
```

## C3 distractor ABCABC (T10_distractor_abcabc)

```
operator -> red blue green red blue green  # target digest=9cd0ca7a79c87064
operator -> kettle pot kettle pot           # distractor digest != target
operator -> moss fern moss fern             # distractor digest != target
operator -> cat dog bird cat dog bird       # probe digest=9cd0ca7a79c87064

prior_acquired_observed=True   transfer_observed=True   verdict=PASS
```

## Aggregate

```
osmotic_live_test version=phase3.25.v1 trials=10 pass=10 warn=0 fail=0
na=0 fp=0 fn=0 transfer_success=7
digest=7aa91075cd76ea73
real_model_calls=0  cache_writes=0  forbidden_term_hits=0
```
