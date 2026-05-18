# PHASE3_22B_LEARNING_PROOF_SPEC.md

## What "structural learning" means here

In Phase 3.22b, "structural learning" is the **observable
acquisition, reuse, or update of bounded structural records** by the
runtime under deterministic operator interaction. It is NOT memory in
the psychological sense. It is NOT semantic understanding. It is NOT
agency, will, desire, belief, or intent. It is a documented
engineering property: state X advances to state X' under a closed
mapping driven by operator input, and the advance is captured as a
bounded `LearningEvidenceRecord`.

## What does and does not count as proof

| Proof? | What | Why |
|---|---|---|
| Yes | A bounded state transition captured by `LearningEvidenceRecord` | Deterministic, printable, replayable, observable |
| Yes | A digest stable across two runs | Determinism witness |
| Yes | A reply that cites a prior acquired/reused record | Reuse witness |
| Yes | A renamed input mapping to the same `abstract_pattern_digest` | Transfer witness |
| Yes | A repeated REPL command lowering `diminishing_returns_factor` | Diminishing-returns witness |
| Yes | A near-miss REPL hint stored and then cited | Correction witness |
| No | A narrative description of "what the model learned" | Not bounded; not auditable |
| No | A claim that the system "understands" the pattern | Forbidden by non-claim discipline |
| No | A claim that the system "remembers" the input in any subjective sense | Forbidden; "remembers" is psychological |
| No | An aggregate "intelligence score" | Forbidden by non-claim discipline |

## Witness shape

For each kind below, the witness is a `LearningEvidenceRecord` whose
`kind` field is the corresponding enum member.

### LearningEvidenceKind.OBSERVED

Initial observation of an input has no prior record. Emitted on the
first observation of every previously-unseen abstract pattern shape.
Witness fields: `kind=OBSERVED`, `interaction_id`,
`abstract_pattern_digest`, `pre_facts=()`, `post_facts=(("entries",
"1"),)`, `summary="observed novel abstract pattern"`.

### LearningEvidenceKind.RECURRENCE_INCREASED

The exact text appears again. Witness records `pre.seed_recurrence`
and `post.seed_recurrence` and asserts post > pre. `summary="seed
recurrence climbed from <pre> to <post>"`.

### LearningEvidenceKind.ABSTRACT_PATTERN_ACQUIRED

A new abstract-pattern shape (per `AbstractPatternSignature.digest`)
is recorded for the first time in this session. `summary="abstract
pattern <digest> acquired"`.

### LearningEvidenceKind.ABSTRACT_PATTERN_REUSED

A previously-acquired abstract-pattern digest is observed again, with
the same or different surface tokens. `summary="abstract pattern
<digest> reused (this is reuse N)"`.

### LearningEvidenceKind.TRANSFER_RECOGNIZED

A subset of REUSED: same abstract-pattern digest, but a strictly
different concrete `pattern_id`. `summary="abstract pattern <digest>
transferred from <prior_pattern_id> to <new_pattern_id>"`.

### LearningEvidenceKind.REPL_CORRECTION_APPLIED

A near-miss REPL line is observed; the bridge's
`near_miss_hint_summary` field is non-empty. On the next valid REPL
line for the same canonical form, the loop emits a record citing the
prior near miss. `summary="near-miss correction applied: <hint> ->
<canonical>"`.

### LearningEvidenceKind.DIMINISHING_RETURNS_UPDATED

A repeated valid REPL command's `diminishing_returns_factor_str`
changes. Witness records the prior and current factor strings.
`summary="diminishing-returns factor <prior> -> <current>"`.

### LearningEvidenceKind.LIMITATION_RECORDED

A REFUSAL or coherence-WARN/FAIL disposition is emitted. Witness
records the disposition and the limitation reason category.
`summary="limitation recorded: <disposition>"`.

## Proof obligations

The benchmark A8 axis exercises each obligation:

1. Before exposure, the session's `LearningEvidenceTrace` has no
   record whose `abstract_pattern_digest` equals the target. (A8.02)
2. After exposure, that record exists. (A8.02)
3. On a renamed input with the same abstract-pattern digest, a
   `TRANSFER_RECOGNIZED` record is emitted. (A8.03)
4. A later reply's `LIMITATION_REPORT` or `NEXT_ACTION_SUGGESTION`
   section cites the prior record by digest fragment. (A8.04)
5. Repeated REPL valid-effective commands generate
   `DIMINISHING_RETURNS_UPDATED` records. (A8.06)
6. A near-miss followed by a valid command emits a
   `REPL_CORRECTION_APPLIED` record. (A8.05)
7. Two runs of the same operator-input sequence produce equal
   `LearningProofReport.digest_hex16`. (A8.07)
8. Exact recurrence emits `RECURRENCE_INCREASED`. (A8.01)

## Determinism witness

`learning_proof_digest_hex16` is the first 16 hex chars of the
SHA-256 over the canonical serialization of all records in the
trace. Determinism implies bit-identical digests across two runs.
The benchmark A8.07 emits two runs and compares.

## Bounded constants

- `LEARNING_TRACE_MAX_RECORDS = 256`
- `LEARNING_RECORD_SUMMARY_MAX_LEN = 240`
- `LEARNING_FACT_KEY_MAX_LEN = 32`
- `LEARNING_FACT_VALUE_MAX_LEN = 64`
- `LEARNING_FACTS_MAX_ENTRIES = 8`
- `ABSTRACT_PATTERN_MAX_TOKENS = 32`
- `ABSTRACT_PATTERN_DIGEST_HEX_LEN = 16`

## What the proof report contains

`PHASE3_22B_LEARNING_PROOF_REPORT.md` (Step 8 deliverable) carries a
table with columns: `case_id`, `input sequence`, `pre-state
structural facts`, `post-state structural facts`, `evidence record
emitted`, `later reuse / transfer event`, `reply excerpt`,
`deterministic digest`, `verdict`. Each row corresponds to one
benchmark A8 case (or a higher-level scenario combining A8 cases).
