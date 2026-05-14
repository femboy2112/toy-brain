# Updating the spec from GitHub

## Source of truth

The canonical Lean source for TLICA / TOCE lives at:

**https://github.com/femboy2112/lean-scratch**

**Read-only.** Do not push to this repository. Clone, pull, and diff only.

The `lean_reference/` directory in this package is a snapshot taken at the time the v0.2 catalog was authored. When the upstream Lean evolves — new theorems land, theorems get renamed, deferred markers resolve into real theorems, new modules appear — the catalog needs to be re-aligned. This file documents the refresh protocol.

## Refresh protocol

### 1. Pull the upstream snapshot

```bash
git clone https://github.com/femboy2112/lean-scratch /tmp/lean-scratch-latest
# or, if already cloned:
cd /tmp/lean-scratch-latest && git fetch origin && git checkout origin/main
```

### 2. Diff against the local snapshot

```bash
diff -ruN lean_reference/TLICA /tmp/lean-scratch-latest/TLICA \
  | tee /tmp/tlica-diff.patch

diff -u lean_reference/TLICA.lean /tmp/lean-scratch-latest/TLICA.lean
```

Two outcomes worth handling specifically:

- **New file under `TLICA/`** (e.g., a new module added to the architecture): grep `INVARIANT_CATALOG.md` to confirm it has no rows yet; if not, propose new rows for any non-deferred theorems in that file.
- **Removed declaration** (theorem renamed or deleted upstream): grep the catalog for the old name; every row citing it needs to be updated or marked DEPRECATED.

### 3. Extract the upstream declaration index

The fastest way to enumerate what changed semantically (not just textually) is to re-run the declaration extractor over the new files:

```bash
for f in /tmp/lean-scratch-latest/TLICA/*.lean /tmp/lean-scratch-latest/TLICA/ProfileComparison/*.lean; do
  echo "=== ${f##*/lean-scratch-latest/} ==="
  grep -nE '^(theorem|def|structure|class|inductive|abbrev|noncomputable def)' "$f"
done > /tmp/upstream-decls.txt
```

Compare against the citations already in the catalog:

```bash
grep -oE '`[A-Za-z]+\.lean::[A-Za-z_]+`' INVARIANT_CATALOG.md \
  | sort -u > /tmp/catalog-citations.txt
```

Any citation in `/tmp/catalog-citations.txt` that does not appear (with matching file + decl name) in `/tmp/upstream-decls.txt` is a stale row.

### 4. For each row that cites a changed declaration, check four conditions

1. **Does the cited declaration still exist?** If renamed, update the row's `Lean source` cell to the new name. If deleted, mark the row's Status as `DEPRECATED` and audit downstream Python code that depended on the corresponding assertion.
2. **Is the proposition still the same?** If the statement changed (e.g., a hypothesis was strengthened or weakened), update the row's `Proposition` and `Python assertion` cells. The row ID stays the same.
3. **Did a `deferred_marker_not_theorem` resolve into a real theorem upstream?** Move the row from `DEFERRED` to `REQUIRED`, write a real Python assertion, and assign a fixture. Add a corresponding entry to the v0 fixture roster if a new fixture file is needed.
4. **Did a new substantive theorem appear that should be in the catalog?** Add a new row with the next available ID for the relevant module section.

### 5. Update the inherited-deferrals table

If `CLAIM_GUARDRAILS.md` upstream changed its deferrals list (RCX, named affect taxonomy, stochastic projection, contestable-boundary, phenomenological duration, free-will branch semantics, …), bring those changes into the catalog's "Inherited deferrals" table verbatim.

### 6. Re-verify summary counts

```bash
echo "REQUIRED: $(grep -c '| REQUIRED |' INVARIANT_CATALOG.md)"
echo "STRUCTURAL: $(grep -c '| STRUCTURAL |' INVARIANT_CATALOG.md)"
echo "NOT-EXERCISED: $(grep -c '| NOT-EXERCISED |' INVARIANT_CATALOG.md)"
echo "DEFERRED: $(grep -c '| DEFERRED |' INVARIANT_CATALOG.md)"
```

Update the "Summary counts" block at the bottom of the catalog if any of these drift.

### 7. Bump the catalog version banner

`v0.2 → v0.3` (or the next appropriate number) in the banner at the top of `INVARIANT_CATALOG.md`. List the substantive changes in the same banner.

### 8. Refresh the local snapshot

Once the catalog is updated and verified, replace `lean_reference/` with the upstream snapshot so the package's offline copy matches the catalog's citations:

```bash
rm -rf lean_reference/TLICA
cp -r /tmp/lean-scratch-latest/TLICA lean_reference/TLICA
cp /tmp/lean-scratch-latest/TLICA.lean lean_reference/TLICA.lean
```

(If the upstream TOCE bundle has a new `TOCE_Core.lean`, refresh that too.)

### 9. Re-run the invariant runner

Any newly REQUIRED row must drive a fixture and the runner must report it green before the spec update is considered done:

```bash
python -m brain.invariants run
```

If the upstream change is large (many new theorems, structural reshape of a module), the runner may regress on previously-green rows because the Python module now needs to be revised to match the new spec. That's expected. The catalog update and the code update are one workflow, not two.

## Where the canonical authority sits in conflicts

If the catalog disagrees with the upstream Lean source, the upstream Lean wins. Update the catalog to match. The catalog is the projection of the Lean spec into Python-runtime terms; if the projection has drifted, fix the projection, not the spec.

If the local snapshot in `lean_reference/` disagrees with the upstream, the upstream wins. Refresh the snapshot.

If the Python code disagrees with the catalog (e.g., the code is satisfying an invariant the catalog says is deferred, or vice versa), the catalog wins. Update the code to match.

## What not to do

- Don't introduce new Python modules outside the catalog's module map without first adding rows for them.
- Don't re-enable a deferred item (RCX, named affect taxonomy, love-as-constitutive-extension, substrate affect pathways, source-opacity affect, stochastic projection, phenomenological duration, temporal continuity metric, contestable-boundary refinement, free-will branch semantics, φ-coordinate / non-Archimedean δ) without an explicit upstream change in the Lean spec or `CLAIM_GUARDRAILS.md`.
- Don't push to `femboy2112/lean-scratch`. It is read-only from this package's perspective.
- Don't relax a numeric or type convention silently. If `Fraction` becomes infeasible for some new theorem, the catalog must be updated to record the new convention and explain why.

## Reading order if the upstream has drifted significantly

For a large upstream change, read in this order before patching the catalog:

1. `lean-scratch/AGENTS.md` — current operating policy, in-scope vs out-of-scope.
2. `lean-scratch/CLAIM_GUARDRAILS.md` — current deferred list and the status vocabulary.
3. `lean-scratch/MAPPING.md` — current declaration map; this is the most reliable cross-reference between Lean declarations and their architectural role.
4. The individual Lean files for any rows you're updating.

The local `lean_reference/` snapshot is for offline work; the upstream is canonical at any moment that asks "what does the theory actually say right now?"
