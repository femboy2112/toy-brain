"""Phase 3.9 persistence load-through-builders fixture.

Drives:

* ``I-PERSIST-05`` (REQUIRED) — Load reconstructs kernel state through
  the existing public builders / constructors only. The fixture
  combines a static AST audit over ``brain/ui/persistence.py`` with a
  behavioural test that confirms the load path actually calls the
  documented builders.
"""
from __future__ import annotations

import ast
import pathlib
import tempfile
from fractions import Fraction
from types import MappingProxyType

from brain.invariants import register
from brain.io_types import ContentRegistry
from brain.tick import BrainState
from brain.tlica import builders as _tlica_builders
from brain.tlica.builders import (
    make_msi,
    make_profile_with_cogito,
    make_ptcns,
)
from brain.tlica.profile import COGITO_ID
from brain.tlica.ptcns import ConsistencyEval
from brain.development import text_stream as _text_stream
from brain.ui.persistence import (
    SessionStoreConfig,
    load_session,
    save_session,
)
from brain.ui.session import OperatorSession


_PERSISTENCE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "persistence.py"
)


_REQUIRED_BUILDER_NAMES: frozenset[str] = frozenset({
    "make_profile_with_cogito",
    "make_msi",
    "make_ptcns",
    "make_text_stream_chunk",
    "make_stream_promotion_candidate",
})


_FORBIDDEN_KERNEL_RECORD_SETATTR_TARGETS: frozenset[str] = frozenset({
    "profile",
    "msi",
    "ptcns",
    "registry",
    "state",
    "values",
    "domain",
    "contents",
    "threshold",
    "eval_map",
    "texts",
    "chunks",
})


def _build_session() -> OperatorSession:
    from brain.development.text_stream import (
        TextStreamHistory,
        TextStreamSource,
        make_text_stream_chunk,
    )
    profile = make_profile_with_cogito(
        {COGITO_ID: 1, "alpha": Fraction(2, 5)}
    )
    msi = make_msi(profile, contents={COGITO_ID, "alpha"}, threshold=Fraction(1, 4))
    ptcns = make_ptcns(
        msi,
        eval_map={
            COGITO_ID: ConsistencyEval.PRESERVE,
            "alpha": ConsistencyEval.PRESERVE,
        },
    )
    registry = ContentRegistry(texts=MappingProxyType({"alpha": "alpha text"}))
    state = BrainState(profile=profile, msi=msi, ptcns=ptcns, registry=registry)
    history = TextStreamHistory(
        chunks=(
            make_text_stream_chunk(
                chunk_id="strm-chunk-1",
                text="builder routing audit chunk",
                source=TextStreamSource.OPERATOR,
                provenance="audit-1",
            ),
        )
    )
    return OperatorSession(state=state, tick_counter=1, stream_history=history)


def _audit_static() -> list[str]:
    errors: list[str] = []
    source = _PERSISTENCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PERSISTENCE_PATH))

    builder_calls_found: set[str] = set()

    for node in ast.walk(tree):
        # Reject `state.profile = ...` / `state.ptcns = ...` etc. on
        # frozen records.
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if target.attr in _FORBIDDEN_KERNEL_RECORD_SETATTR_TARGETS:
                        errors.append(
                            f"forbidden attribute assignment to "
                            f".{target.attr} at line {target.lineno}"
                        )
        if isinstance(node, ast.AugAssign):
            target = node.target
            if isinstance(target, ast.Attribute):
                if target.attr in _FORBIDDEN_KERNEL_RECORD_SETATTR_TARGETS:
                    errors.append(
                        f"forbidden augmented-assignment to .{target.attr} "
                        f"at line {target.lineno}"
                    )
        # Reject `object.__setattr__(record, "field", ...)`.
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                if (
                    isinstance(func.value, ast.Name)
                    and func.value.id == "object"
                    and func.attr == "__setattr__"
                ):
                    errors.append(
                        f"forbidden object.__setattr__ call at line "
                        f"{node.lineno}"
                    )
            # Track builder calls.
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name and name in _REQUIRED_BUILDER_NAMES:
                builder_calls_found.add(name)
        # Reject `pickle.loads(...)` / `shelve.open(...)` /
        # `marshal.loads(...)`.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr_chain = node.func
            if isinstance(attr_chain.value, ast.Name):
                pair = (attr_chain.value.id, attr_chain.attr)
                if pair in {
                    ("pickle", "loads"),
                    ("pickle", "load"),
                    ("shelve", "open"),
                    ("marshal", "loads"),
                    ("marshal", "load"),
                    ("dill", "loads"),
                    ("cloudpickle", "loads"),
                }:
                    errors.append(
                        f"forbidden {attr_chain.value.id}.{attr_chain.attr}() "
                        f"call at line {node.lineno}"
                    )

    missing = _REQUIRED_BUILDER_NAMES - builder_calls_found
    if missing:
        errors.append(
            f"load path does not call required builders: "
            f"{sorted(missing)!r}"
        )
    return errors


def _audit_behavioural() -> list[str]:
    """Patch each builder with a counting wrapper and verify load calls it."""
    errors: list[str] = []
    counts: dict[str, int] = {name: 0 for name in _REQUIRED_BUILDER_NAMES}

    originals: dict[str, object] = {}
    targets: dict[str, object] = {
        "make_profile_with_cogito": _tlica_builders,
        "make_msi": _tlica_builders,
        "make_ptcns": _tlica_builders,
        "make_text_stream_chunk": _text_stream,
        "make_stream_promotion_candidate": _text_stream,
    }
    # Save originals and patch.
    for name, mod in targets.items():
        originals[name] = getattr(mod, name)

    def _wrap(name: str, original):
        def _wrapper(*args, **kwargs):
            counts[name] += 1
            return original(*args, **kwargs)
        return _wrapper

    # The persistence module imported the builders at module load time
    # so monkeypatching the source module isn't enough; we also need to
    # patch the binding in the persistence module's namespace.
    import brain.ui.persistence as _persistence  # noqa: PLC0415

    persistence_originals: dict[str, object] = {}
    for name in targets:
        persistence_originals[name] = getattr(_persistence, name, None)

    try:
        for name, mod in targets.items():
            wrapped = _wrap(name, originals[name])
            setattr(mod, name, wrapped)
            if hasattr(_persistence, name):
                setattr(_persistence, name, wrapped)

        session = _build_session()
        with tempfile.TemporaryDirectory(prefix="brain-persist-05-") as td:
            db_path = pathlib.Path(td) / "session.sqlite3"
            config = SessionStoreConfig(db_path=db_path)
            save_session(session, config)
            load_session(config)
    finally:
        for name, mod in targets.items():
            setattr(mod, name, originals[name])
            if persistence_originals[name] is not None:
                setattr(_persistence, name, persistence_originals[name])

    # Every builder must have been called at least once during load.
    for name in ("make_profile_with_cogito", "make_msi", "make_ptcns",
                 "make_text_stream_chunk"):
        if counts[name] < 1:
            errors.append(
                f"load_session did not call {name} (count = "
                f"{counts[name]})"
            )
    return errors


@register("I-PERSIST-05", status="REQUIRED")
def check_i_persist_05_load_constructor_only() -> None:
    """Static + behavioural audit that load routes through builders."""
    errors: list[str] = []
    errors.extend(_audit_static())
    errors.extend(_audit_behavioural())
    if errors:
        raise AssertionError(
            "I-PERSIST-05 violated:\n  - " + "\n  - ".join(errors)
        )
