Spawn the `brain-catalog-lint` agent and report its punch list verbatim.

Read-only by default. If the user explicitly names a finding and asks to apply
mechanical fixes, only C1 (banner rewrite) and C2 (FIXTURE_MODULES list
append/remove) are auto-applyable. C3 and C4 require user judgment.

Never commit or push from this command. Surface fixes as suggested edits; the
user decides what to commit and on which branch.
