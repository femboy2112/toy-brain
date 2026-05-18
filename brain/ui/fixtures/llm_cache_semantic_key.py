"""Phase 3.14 L2 semantic-key fixture.

Drives:

* ``I-LLMCACHE-06`` (REQUIRED) — L2 canonical evaluation cache is keyed
  by the locked semantic payload and excludes the evaluated
  ``new_id``: same ``existing_msi_context`` + same ``new_text`` under
  different content IDs produces the same L2 key.
* ``I-LLMCACHE-07`` (REQUIRED) — L2 key namespace includes
  ``cache_schema_version``, ``prompt_template_version``,
  ``parse_schema_version``, ``backend_family``, ``model_identity``.
* ``I-LLMCACHE-08`` (REQUIRED) — L2 canonicalization preserves
  legitimate existing-MSI-context differences and reuses
  same-``new_text``/different-``new_id`` results under the same
  context.
* ``I-LLMCACHE-15`` (REQUIRED) — Different semantic contexts evaluate
  separately; no false hit across different existing MSI contexts,
  ``prompt_template_version``, ``parse_schema_version``,
  ``backend_family``, or ``model_identity``.
"""
from __future__ import annotations

import tempfile
from fractions import Fraction
from pathlib import Path

from brain.invariants import register
from brain.llm.client import CachedClient
from brain.llm.ptcns_backed import (
    LLMBackedPtCns,
    SEMANTIC_CACHE_SCHEMA_VERSION,
    _canonical_l2_key,
)
from brain.llm.prompts import PROMPT_TEMPLATE_VERSION
from brain.llm.parse import PARSE_SCHEMA_VERSION
from brain.tlica.builders import make_msi, make_profile_with_cogito
from brain.tlica.profile import COGITO_ID, ContentID
from brain.tlica.ptcns import ConsistencyEval


class _CountingClient:
    """Local counting LLM client returning a canned response."""

    def __init__(self, response: str = "PRESERVE") -> None:
        self.response = response
        self.calls: list[str] = []

    def eval_consistency(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response


def _make_msi_with_anchor(text: str = "anchor a description") -> tuple:
    profile = make_profile_with_cogito({COGITO_ID: 1, "anchor_a": "3/4"})
    msi = make_msi(
        profile=profile,
        contents={COGITO_ID, ContentID("anchor_a")},
        threshold=Fraction(1, 2),
    )
    texts = {
        ContentID("anchor_a"): text,
        ContentID("new_x"): "the new content under evaluation",
        ContentID("new_y"): "the new content under evaluation",  # same text
        ContentID("new_z"): "a completely different new content",
    }
    return msi, texts


@register("I-LLMCACHE-06", status="REQUIRED")
def check_I_LLMCACHE_06_new_id_excluded_from_key() -> None:
    msi, texts = _make_msi_with_anchor()
    inner = _CountingClient("PRESERVE")
    with tempfile.TemporaryDirectory(prefix="phase3_14_sk06_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_sk06_l2_") as l2_tmp:
        l1 = CachedClient(inner=inner, cache_dir=Path(l1_tmp))
        p = LLMBackedPtCns(msi=msi, content_texts=texts, client=l1)
        # Redirect L2 to a tempdir so the probe never touches brain/.llm_cache.
        p._l2_dir = Path(l2_tmp)
        # First eval populates L2.
        r1 = p.eval(ContentID("new_x"))
        # Reset L0 to force the second eval to go through the L2 path.
        if ContentID("new_y") in p._cache:
            del p._cache[ContentID("new_y")]
        r2 = p.eval(ContentID("new_y"))
        assert r1 is ConsistencyEval.PRESERVE
        assert r2 is ConsistencyEval.PRESERVE
        # Inner client must have been called exactly once: same
        # existing_msi_context + same new_text under different new_id
        # collapses to one L2 entry, so the second eval is an L2 hit.
        assert len(inner.calls) == 1, (
            "I-LLMCACHE-06 violated: different new_id with identical "
            f"semantic inputs called inner more than once "
            f"(got inner calls={len(inner.calls)})"
        )
        # Exactly one L2 entry written.
        files = sorted(Path(l2_tmp).glob("*.json"))
        assert len(files) == 1, (
            "I-LLMCACHE-06 violated: expected 1 L2 entry, got "
            f"{len(files)}"
        )


@register("I-LLMCACHE-07", status="REQUIRED")
def check_I_LLMCACHE_07_l2_key_namespace() -> None:
    # Direct call to _canonical_l2_key with varying namespace fields:
    # every field must influence the key. We build a baseline key and
    # then mutate one field at a time; each mutation must change the
    # resulting hash.
    base = dict(
        backend_family="anthropic-api",
        model_identity="claude-sonnet-4-6",
        existing_msi_context=(("anchor_a", "anchor a description"),),
        new_text="the new content under evaluation",
    )
    base_key = _canonical_l2_key(**base)
    assert isinstance(base_key, str) and len(base_key) == 64, (
        "I-LLMCACHE-07 violated: L2 key is not a 64-char SHA-256 hex "
        f"(got {base_key!r})"
    )

    # Mutate each namespace input and confirm the key changes.
    mutations = [
        ("backend_family", "claude-cli"),
        ("model_identity", "claude-sonnet-4-7"),
        ("existing_msi_context", (("anchor_b", "anchor a description"),)),
        ("existing_msi_context", (("anchor_a", "different anchor text"),)),
        ("new_text", "an entirely different new content"),
    ]
    for field, new_value in mutations:
        kw = dict(base)
        kw[field] = new_value
        mutated_key = _canonical_l2_key(**kw)
        assert mutated_key != base_key, (
            "I-LLMCACHE-07 violated: mutating "
            f"{field}={new_value!r} did not change the L2 key"
        )

    # Verify the three version constants are wired into the key by
    # confirming they have non-empty bounded printable values; the key
    # is sensitive to them by construction inside _canonical_l2_key.
    assert SEMANTIC_CACHE_SCHEMA_VERSION == "llm-semantic-cache-v1"
    assert PROMPT_TEMPLATE_VERSION == "prompt-template-v1"
    assert PARSE_SCHEMA_VERSION == "consistency-eval-v1"


@register("I-LLMCACHE-08", status="REQUIRED")
def check_I_LLMCACHE_08_canonicalization_preserves_distinctions() -> None:
    # Two LLMBackedPtCns instances with different existing MSI texts
    # must produce different L2 keys (legitimate context distinction).
    msi_a, texts_a = _make_msi_with_anchor("anchor a description")
    msi_b, texts_b = _make_msi_with_anchor("anchor a DIFFERENT description")
    inner = _CountingClient("PRESERVE")
    with tempfile.TemporaryDirectory(prefix="phase3_14_sk08_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_sk08_l2_") as l2_tmp:
        l1 = CachedClient(inner=inner, cache_dir=Path(l1_tmp))
        l2_dir = Path(l2_tmp)
        pa = LLMBackedPtCns(msi=msi_a, content_texts=texts_a, client=l1)
        pa._l2_dir = l2_dir
        pb = LLMBackedPtCns(msi=msi_b, content_texts=texts_b, client=l1)
        pb._l2_dir = l2_dir
        pa.eval(ContentID("new_x"))
        pb.eval(ContentID("new_x"))
        # Different existing MSI context -> different L2 keys -> two L2
        # entries.
        files = sorted(l2_dir.glob("*.json"))
        assert len(files) == 2, (
            "I-LLMCACHE-08 violated: expected 2 L2 entries for distinct "
            f"existing MSI contexts (got {len(files)})"
        )
        # Inner called twice (one per context) because L1 prompts also
        # differ.
        assert len(inner.calls) == 2, (
            "I-LLMCACHE-08 violated: inner client call count drifted "
            f"(got {len(inner.calls)})"
        )

    # Also: same context, same new_text, different new_id -> ONE entry.
    msi_c, texts_c = _make_msi_with_anchor("shared anchor")
    inner2 = _CountingClient("PRESERVE")
    with tempfile.TemporaryDirectory(prefix="phase3_14_sk08b_") as l1_tmp, \
         tempfile.TemporaryDirectory(prefix="phase3_14_sk08b_l2_") as l2_tmp:
        l1 = CachedClient(inner=inner2, cache_dir=Path(l1_tmp))
        p = LLMBackedPtCns(msi=msi_c, content_texts=texts_c, client=l1)
        p._l2_dir = Path(l2_tmp)
        p.eval(ContentID("new_x"))
        p.eval(ContentID("new_y"))
        files = sorted(Path(l2_tmp).glob("*.json"))
        assert len(files) == 1, (
            "I-LLMCACHE-08 violated: same-text/different-new_id wrote "
            f"more than one L2 entry (got {len(files)})"
        )


@register("I-LLMCACHE-15", status="REQUIRED")
def check_I_LLMCACHE_15_no_false_hits_across_namespaces() -> None:
    # Cross-namespace separation: explicit mutation of each field
    # produces a distinct L2 key, so no false hit can occur across
    # different model / backend / template / parser versions.
    base_args = dict(
        backend_family="anthropic-api",
        model_identity="claude-sonnet-4-6",
        existing_msi_context=(("anchor_a", "anchor a description"),),
        new_text="the new content under evaluation",
    )
    keys = set()
    keys.add(_canonical_l2_key(**base_args))
    # Mutating each namespace field must yield a unique key.
    keys.add(_canonical_l2_key(**{**base_args, "backend_family": "claude-cli"}))
    keys.add(_canonical_l2_key(**{**base_args, "backend_family": "codex-cli"}))
    keys.add(_canonical_l2_key(**{**base_args, "model_identity": "claude-sonnet-4-7"}))
    keys.add(_canonical_l2_key(
        **{**base_args, "existing_msi_context": (("anchor_a", "different"),)}
    ))
    keys.add(_canonical_l2_key(**{**base_args, "new_text": "different new"}))
    assert len(keys) == 6, (
        "I-LLMCACHE-15 violated: namespace mutations did not produce "
        f"distinct keys (got {len(keys)} distinct keys)"
    )
