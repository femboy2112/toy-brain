# ARCHIVE

Historical content that was previously in `README.md` but no longer reflects
the current state of the repository. Kept for context — the kernel was built
following this order, and the prohibitions documented here are still useful
when reading the v0 commits.

The canonical entry point is `README.md` (current) and the live
`INVARIANT_CATALOG.md`. Treat anything in this file as a record of past
state, not as instructions for new work.

## Historical v0 build order

From the original v0 kickoff. The eight-file checkpoint listed below has
long since been green; the kernel has expanded substantially past it. This
order is preserved verbatim for archival purposes.

> Do **not** start with `tick.py`. Build in this order:
>
> 1. `brain/tlica/profile.py`
> 2. `brain/tlica/msi.py`
> 3. `brain/tlica/ptcns.py`
> 4. `brain/tlica/builders.py`
> 5. `brain/validation.py`
> 6. `brain/invariants.py` (catalog registry + runner shell)
> 7. `brain/fixtures/minimal.py`
> 8. `brain/fixtures/cogito_invariants.py`
>
> At this point run `python -m brain.invariants run`. The runner should
> report green on every REQUIRED row owned by those eight files (these
> fixtures cover I-PROF-01..02, I-MSI-01..06, I-PTC-01..05, I-MOD-04,
> I-IBND-02, I-PRES-01..05).
>
> Once that gate is green, expand to the remaining modules in the
> dependency order implied by the import graph:
>
> - `preservation.py` → `project_map.py` → `pce.py` → `action_projection.py`
>   → `agency.py` → `trajectory.py` → `affect.py`
> - `comparison/pointwise.py` can be built in parallel with the above
> - `iboundary.py` after `ptcns.py`
> - `toce_core.py` is independent of `brain/tlica/`
>
> Then add the remaining fixtures: `content_classification.py`,
> `profile_distance.py`, `mode_a_dispatch.py`, `mode_c_dispatch.py`,
> `neutral_encapsulation.py`, `action_selection.py`, `projected_pce.py`,
> `affect_kernel_collapse.py`, `trajectory_step.py`.
>
> Only after every REQUIRED row is green should you implement
> `brain/tick.py` and `brain/io_types.py`.

## Historical v0 "Things to not do"

From the original v0 kickoff. The items that remain authoritative (no
`typing.Literal` for `Act`, no raw `float` in `brain/tlica/`, no deferred-
item revival, no push to `femboy2112/lean-scratch`) were retained in
`README.md`. The items below were v0-specific and no longer apply.

> - Don't review the plan. Implement v0.2 exactly.
> - Don't write `brain/tick.py` until the eight-file checkpoint is green.

Both are obsolete: the catalog is now v0.5 and `brain/tick.py` is shipped.
