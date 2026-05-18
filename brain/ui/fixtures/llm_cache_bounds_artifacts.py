"""Phase 3.14 L2 bounds + sensitive-artifact fixture.

Drives:

* ``I-LLMCACHE-11`` (REQUIRED) — L2 cache growth is bounded: max 1024
  entries; at cap, hits still read, misses may call the inner path but
  do not write a new entry, and ``llm.semantic_cache_skip`` fires with
  ``reason="capacity"``.
* ``I-LLMCACHE-12`` (REQUIRED) — L1 / L2 cache files are sensitive
  local artifacts: gitignored; no raw prompt / raw response appears in
  committed docs / fixtures / test outputs; the L2 entry schema is
  exactly ``{"key_prefix", "parsed"}``.
"""
from __future__ import annotations

import json
import tempfile
from fractions import Fraction
from pathlib import Path

from brain.invariants import register
from brain.llm.client import CachedClient
from brain.llm.ptcns_backed import (
    LLMBackedPtCns,
    SEMANTIC_CACHE_DIR,
    SEMANTIC_CACHE_MAX_ENTRIES,
)
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval
from brain.trace import MemoryTracer


class _CountingClient:
    def __init__(self, response: str = "PRESERVE") -> None:
        self.response = response
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response


def _make_msi(extra_text: str = "anchor a description") -> tuple:
    profile = make_profile_with_cogito({COGITO_ID: 1, "anchor_a": "3/4"})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("anchor_a")},
        threshold=Fraction(1, 2),
    )
    return msi, extra_text


@register("I-LLMCACHE-11", status="REQUIRED")
def check_I_LLMCACHE_11_l2_capacity_bound() -> None:
    # Exercise capacity behavior without writing 1024 real evaluations:
    # pre-populate the L2 dir with SEMANTIC_CACHE_MAX_ENTRIES synthetic
    # entries so the next miss triggers the capacity-skip branch.
    assert SEMANTIC_CACHE_MAX_ENTRIES == 1024, (
        "I-LLMCACHE-11 violated: cap drifted "
        f"(got {SEMANTIC_CACHE_MAX_ENTRIES})"
    )
    msi, _ = _make_msi()
    texts = {
        ContentID("anchor_a"): "anchor a description",
        ContentID("new_x"): "the new content under evaluation",
    }
    inner = _CountingClient("PRESERVE")
    tracer = MemoryTracer()
    with tempfile.TemporaryDirectory(prefix="phase3_14_b11_l1_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_b11_l2_") as l2_tmp:
        l1 = CachedClient(inner=inner, cache_dir=Path(l1_tmp))
        l2_dir = Path(l2_tmp)
        # Pre-fill the L2 dir with bounded printable filler entries.
        for i in range(SEMANTIC_CACHE_MAX_ENTRIES):
            filler = l2_dir / f"{i:064d}.json"
            filler.write_text(
                json.dumps({"key_prefix": f"{i:08x}"[:8], "parsed": "PRESERVE"}),
                encoding="utf-8",
            )
        p = LLMBackedPtCns(
            msi=msi, content_texts=texts, client=l1, tracer=tracer
        )
        p._l2_dir = l2_dir
        result = p.eval(ContentID("new_x"))
        assert result is ConsistencyEval.PRESERVE
        # Inner was called once (capacity skip still allows the miss
        # path to invoke the inner client).
        assert len(inner.calls) == 1, (
            "I-LLMCACHE-11 violated: capacity skip changed inner-call "
            f"discipline (got inner calls={len(inner.calls)})"
        )
        # No new L2 entry was written.
        files = sorted(l2_dir.glob("*.json"))
        assert len(files) == SEMANTIC_CACHE_MAX_ENTRIES, (
            "I-LLMCACHE-11 violated: at-cap miss wrote a new L2 entry "
            f"(got {len(files)} files)"
        )
        # Tracer must have emitted llm.semantic_cache_skip with
        # reason="capacity".
        skip_events = [e for e in tracer.events if e["type"] == "llm.semantic_cache_skip"]
        assert any(e.get("reason") == "capacity" for e in skip_events), (
            "I-LLMCACHE-11 violated: no llm.semantic_cache_skip event "
            f"with reason='capacity' (events={skip_events!r})"
        )

    # Below cap: a new L2 entry is written normally.
    inner = _CountingClient("PRESERVE")
    with tempfile.TemporaryDirectory(prefix="phase3_14_b11b_l1_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_b11b_l2_") as l2_tmp:
        l1 = CachedClient(inner=inner, cache_dir=Path(l1_tmp))
        p = LLMBackedPtCns(
            msi=msi,
            content_texts={
                ContentID("anchor_a"): "anchor a description",
                ContentID("new_x"): "below-cap content",
            },
            client=l1,
        )
        p._l2_dir = Path(l2_tmp)
        p.eval(ContentID("new_x"))
        files = sorted(Path(l2_tmp).glob("*.json"))
        assert len(files) == 1, (
            "I-LLMCACHE-11 violated: below-cap write did not create one "
            f"L2 entry (got {len(files)})"
        )


@register("I-LLMCACHE-12", status="REQUIRED")
def check_I_LLMCACHE_12_sensitive_artifact_discipline() -> None:
    # The L2 cache directory under brain/ is a gitignored subpath of
    # brain/.llm_cache. Confirm the configured path is the expected
    # subdir.
    assert SEMANTIC_CACHE_DIR == Path("brain/.llm_cache") / "eval_v1", (
        "I-LLMCACHE-12 violated: SEMANTIC_CACHE_DIR drifted "
        f"(got {SEMANTIC_CACHE_DIR!r})"
    )

    # Repo root .gitignore must cover brain/.llm_cache so the L2 subdir
    # (eval_v1) is also covered by directory ignore.
    repo_root = Path(__file__).resolve().parents[3]
    gitignore = repo_root / ".gitignore"
    assert gitignore.exists(), (
        "I-LLMCACHE-12 violated: repo root .gitignore not found"
    )
    text = gitignore.read_text(encoding="utf-8")
    assert "brain/.llm_cache/" in text or "brain/.llm_cache" in text, (
        "I-LLMCACHE-12 violated: .gitignore does not cover brain/.llm_cache"
    )

    # Write a synthetic L2 entry into a tempdir and confirm the payload
    # shape is exactly {"key_prefix", "parsed"} with no raw prompt /
    # response keys.
    msi = make_msi(
        profile=make_profile_with_cogito({COGITO_ID: 1, "anchor_a": "3/4"}),
        contents={COGITO_ID, ContentID("anchor_a")},
        threshold=Fraction(1, 2),
    )
    texts = {
        ContentID("anchor_a"): "anchor a description",
        ContentID("new_x"): "the new content under evaluation",
    }
    inner = _CountingClient("PRESERVE")
    with tempfile.TemporaryDirectory(prefix="phase3_14_b12_l1_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_b12_l2_") as l2_tmp:
        l1 = CachedClient(inner=inner, cache_dir=Path(l1_tmp))
        p = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        p._l2_dir = Path(l2_tmp)
        p.eval(ContentID("new_x"))
        files = sorted(Path(l2_tmp).glob("*.json"))
        assert len(files) == 1, (
            "I-LLMCACHE-12 violated: expected one L2 entry, got "
            f"{len(files)}"
        )
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        assert set(payload.keys()) == {"key_prefix", "parsed"}, (
            "I-LLMCACHE-12 violated: L2 entry has unexpected keys "
            f"({sorted(payload.keys())})"
        )
        for forbidden in ("prompt", "response", "raw", "error", "trace", "headers"):
            assert forbidden not in payload, (
                "I-LLMCACHE-12 violated: L2 entry contains forbidden key "
                f"{forbidden!r}"
            )
        # File name is the SHA-256 hex digest (64 chars + ".json").
        assert files[0].stem != "" and len(files[0].stem) == 64, (
            "I-LLMCACHE-12 violated: L2 file name is not a 64-char hex "
            f"digest (got {files[0].name!r})"
        )
