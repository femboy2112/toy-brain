# Phase 3 Developmental Synthesis v0.2

This document bridges the completed catalog v0.5 baseline-hardening cycle into
Phase 3 planning. It is a planning artifact only. It does not authorize Phase 3
runtime implementation.

## 1. Current Baseline

The v0.5 baseline is merged and green. The strict catalog count gate reports:

```text
84 REQUIRED
15 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

v0.5 proves that the current Python kernel preserves the catalog-bound TLICA
structure under deterministic fixtures: profile bounds, cogito invariants,
PtCns partition behavior, mode dispatch, project-map and projected-PCE routing,
agency selection, trajectory distance bounds, TOCE classification, LLM seam
protocol behavior, trace observation discipline, single-event tick semantics,
duplicate content rejection, FutureMSIModel domain guards, and catalog-to-runner
coverage.

v0.5 does not prove that a real LLM will classify human-facing percepts the way
the scripted expectations predict. I-BHV-01 verifies orchestration under a
MockClient seeded from `expected_eval`; it does not certify semantic judgment by
the live backend. The real trace is therefore evidence about backend behavior
under the current prompt, not a failure of the kernel invariants.

## 2. Real Traced Behavioral Result

The committed real trace is:

```text
trace file: traces/first_scenario_real.jsonl
summary file: traces/RUN_SUMMARY.md
kernel health: clean
LLM semantic match: 2/4
```

The trace summary records clean kernel health: all eval, mode, parse, cache,
invariant, and error inspection points were healthy, with first-attempt parse
success on all four ticks and no retry or ambiguity path exercised.

The semantic behavior was:

```text
sunset_on_beach_today             expected PRESERVE  actual DAMAGE
claim_i_am_actually_someone_else  expected DAMAGE    actual DAMAGE
weather_forecast_for_tomorrow     expected NEUTRAL   actual NEUTRAL
self_continuity_with_sunset       expected PRESERVE  actual DAMAGE
```

| Content | Expected | Actual |
|---|---|---|
| `sunset_on_beach_today` | PRESERVE | DAMAGE |
| `claim_i_am_actually_someone_else` | DAMAGE | DAMAGE |
| `weather_forecast_for_tomorrow` | NEUTRAL | NEUTRAL |
| `self_continuity_with_sunset` | PRESERVE | DAMAGE |

The two non-matching rows were both expected to be PRESERVE but were emitted as
DAMAGE by the real backend.

## 3. Interpretation: Cold-Start Conservatism

The trace shows what the LLM emitted; it does not directly prove why.

The strongest working interpretation is cold-start conservatism. In the traced
scenario, the MSI begins as a cogito-only structure. There is no lived content
network around the cogito anchor, no substrate history, and no prior positive
content that would make a new concrete self-related percept fit cleanly into an
already stabilized pattern.

Under that condition, identity-adjacent content may be read as perturbation
rather than preservation. A sunset memory or self-continuity claim can sound
positive to the scenario author while still being structurally underdetermined
for a backend asked to classify consistency against an almost empty self-model.

This is an inference from the observed trace and prompt context, not a theorem
and not a direct statement of the model's internal reason.

## 4. Bridge Principle

PRESERVE should be earned, not labeled.

Phase 3 should build the developmental conditions under which PRESERVE becomes
meaningful. A content should not be treated as preservative merely because its
surface text is pleasant, self-adjacent, or narratively positive. PRESERVE should
arise when the system has enough substrate history, pattern stability,
prediction support, and clean integration context to justify treating the
content as self-model-preserving.

The Phase 3 bridge is therefore not "make the prompt call sunsets PRESERVE."
It is "build the history in which a sunset can become preservative."

## 5. Phase 3.1 Empirical Motivation

```text
In a cogito-only state, identity-adjacent content is not automatically PRESERVE.
Before lived content exists, new content may properly appear as perturbation.
The chamber’s job is to build the substrate history that makes clean integration possible.
```

Phase 3.1 should give the system a pre-symbolic developmental substrate before
expecting stable semantic classifications. The trace motivates a chamber that
accumulates frames, source tags, salience, stability, and prediction gain before
promotion into higher-level percept events.

The key empirical lesson is that cold-start symbolic classification is too thin
to carry developmental meaning by itself. The system needs a place where repeated
contact can become patterned history.

## 6. Phase Order

Use this order for Phase 3 unless explicitly overridden:

```text
Phase 3.1 — Osmotic Chamber
Phase 3.2 — Output ladder
Phase 3.3 — Minimal Worldlet
Phase 3.4 — Proto-BASIC REPL
Phase 3.5 — Expression + ReadabilityPredictor
Phase 3.6 — Social/language harness
```

Worldlet comes before REPL because worldlet causality and not-I pushback are
developmentally more primitive than symbolic Proto-BASIC command syntax. The
system should first encounter structured external regularity and resistance
before it gets a symbolic command language for manipulating that regularity.

The output ladder comes before Worldlet because the system needs constrained
ways to express contact, uncertainty, and proto-intent before external world
interaction becomes meaningful. The later expression/readability and
social/language phases should build on a system that already has substrate
history, outputs, and world contact.

## 7. Phase 3.1 Required Scope

Phase 3.1 must include the following surfaces from day one:

```text
PhenomenalFrame
FrameSource
SubstrateDrives
SubstrateHistory
ProtoPattern
ProtoContent
salience_v1
stability_v1
prediction_gain_v1
SIMILARITY
FOCUS_CONTACT
ProbeUse
ProbePolicyState
promotion gate to PerceptEvent
source-tag audit
first deterministic chamber fixtures
```

`SubstrateHistory` is in scope from day one. It is not a later analytics layer.
Without history, the chamber cannot distinguish a one-off perturbation from a
stabilizing pattern, and PRESERVE remains an externally assigned label rather
than an earned classification.

The promotion gate to `PerceptEvent` should be deterministic at first. Phase 3.1
should make early chamber fixtures inspectable and reproducible before any noisy
or qualitative behavior is treated as evidence.

The source-tag audit should be designed early because `FrameSource` will become
a boundary between internal generation, external contact, probe output, and
later social/language inputs. Source confusion would directly undermine the
developmental reading of stability and prediction gain.

## 8. Status Discipline

Phase 3 rows should use statuses conservatively:

```text
REQUIRED for safety / deterministic gates / kernel-boundary protections
STRUCTURAL for protocols and construction constraints
OBSERVED for noise robustness and qualitative developmental behavior
EXPERIMENTAL only if explicitly added to tooling later
```

Many developmental rows should be OBSERVED, not REQUIRED. A row about a chamber
showing qualitatively interesting salience drift, proto-pattern emergence, or
noise robustness should not block the kernel unless the property is made
deterministic and safety-critical.

The current v0.5 standard should remain intact: REQUIRED and STRUCTURAL rows are
gates; OBSERVED rows are recorded without deciding correctness; DEFERRED rows
are not implemented by implication; catalog status should never be weakened just
to make code pass.

## 9. Scheduled Pre-Phase-3.1 Hardening

Before heavy developmental tracing, schedule reserved-key protection for tracer
payloads. Current tracer payloads can overwrite reserved fields like:

```text
type
timestamp_ns
tick_id
```

This is not part of v0.5, but it should be handled before or inside Phase 3.1
kickoff. Developmental traces will likely carry richer frame, source, probe,
promotion, and history payloads. The trace seam should reject or namespace
payload keys that collide with core envelope fields before those traces become a
primary empirical artifact.

This hardening is a boundary-protection task, not a developmental feature. It is
a good candidate for REQUIRED or STRUCTURAL treatment depending on the exact
catalog row shape chosen at kickoff.

## 10. ClaudeCLIClient Note

ClaudeCLIClient is an optional backend under the existing LLMClient Protocol
seam.
It does not require a new catalog row.
It should remain non-required in fixtures because it depends on local CLI/auth
state.

The real traced run is valuable as an empirical artifact precisely because it is
outside the strict fixture gate. The deterministic MockClient path should remain
the catalog gate for orchestration; local real-backend runs should remain
explicit, documented, and non-required.

## Phase 3.1 Kickoff Implications

The next kickoff should start with a catalog patch, not runtime code. It should
separate kernel-boundary protections from developmental observations, and it
should make the deterministic chamber fixtures small enough that failures
identify a specific construction error.

Recommended kickoff order:

1. Add Phase 3.1 planning rows with conservative statuses.
2. Add trace reserved-key hardening if not handled as a pre-kickoff patch.
3. Define chamber data structures and source tags.
4. Define deterministic salience, stability, and prediction-gain stubs.
5. Define promotion-gate behavior into `PerceptEvent`.
6. Add first deterministic chamber fixtures.
7. Only then consider noisy OBSERVED behavior.

The bridge from v0.5 to Phase 3 is therefore narrow and explicit: keep the
kernel invariant discipline, add a developmental substrate before expecting
semantic preservation, and treat real-backend behavior as evidence to interpret,
not as a fixture oracle to overfit.
