"""Operator transcript fixtures.

Drives:

* ``I-UI-19`` (REQUIRED) — :class:`brain.ui.transcript.OperatorTranscript`
  records UI events copy-on-write and remains local UI state only. The
  ring is bounded by :data:`brain.ui.transcript.TRANSCRIPT_MAX_ENTRIES`;
  text payloads are bounded printable (via
  :data:`brain.ui.transcript.TRANSCRIPT_MAX_TEXT_LEN`); non-printable
  text and non-tag inputs are rejected; an append on a previously
  constructed transcript returns a new value without mutating the
  original (copy-on-write). The transcript holds no callable, file
  handle, socket, or LLM-client value; it is never serialized to a
  trace, scenario, developmental history, or any other persistent
  surface (corrigenda ruling D — no persistence across invocations).

The fixture is pure: it constructs the transcript directly, exercises
every documented append / extend / projection path, and asserts the
pre/post invariants without invoking curses, the kernel, the LLM seam,
the filesystem, the network, or any developmental history.
"""
from __future__ import annotations

import ast
from pathlib import Path

from brain.invariants import register
from brain.ui.layout import TranscriptSnapshot, TranscriptSnapshotEntry
from brain.ui.transcript import (
    ALLOWED_TRANSCRIPT_KINDS,
    OperatorTranscript,
    TRANSCRIPT_MAX_ENTRIES,
    TRANSCRIPT_MAX_TEXT_LEN,
    TranscriptEntry,
    TranscriptKind,
)


# ---------------------------------------------------------------------------
# I-UI-19 — OperatorTranscript records UI events copy-on-write and remains
# local UI state only.
# ---------------------------------------------------------------------------


@register("I-UI-19", status="REQUIRED")
def check_I_UI_19_transcript_is_local_copy_on_write() -> None:
    # ---- Empty constructor / defaults -------------------------------------
    empty = OperatorTranscript.empty()
    assert empty.entries == (), "I-UI-19: empty transcript should have no entries"
    assert empty.limit == TRANSCRIPT_MAX_ENTRIES, (
        f"I-UI-19: default limit must be {TRANSCRIPT_MAX_ENTRIES} "
        f"(got {empty.limit})"
    )
    assert len(empty) == 0
    assert empty.last() is None

    # OperatorTranscript() with no args also gives an empty ring.
    plain = OperatorTranscript()
    assert plain.entries == ()
    assert plain.limit == TRANSCRIPT_MAX_ENTRIES

    # ---- TranscriptKind enumeration is closed ----------------------------
    expected_kinds = {"SUBMIT", "QUEUED", "STEP", "ERROR", "VIEW", "QUIT"}
    actual_kinds = {k.value for k in TranscriptKind}
    assert actual_kinds == expected_kinds, (
        f"I-UI-19: TranscriptKind drifted; expected {sorted(expected_kinds)!r}, "
        f"got {sorted(actual_kinds)!r}"
    )
    assert ALLOWED_TRANSCRIPT_KINDS == frozenset(expected_kinds), (
        "I-UI-19: ALLOWED_TRANSCRIPT_KINDS must mirror TranscriptKind values"
    )

    # ---- TranscriptEntry validation --------------------------------------
    good = TranscriptEntry(kind=TranscriptKind.SUBMIT, tick_at_event=0, text="hi")
    assert good.kind is TranscriptKind.SUBMIT
    assert good.tick_at_event == 0
    assert good.text == "hi"

    # kind must be a TranscriptKind, not a plain str.
    try:
        TranscriptEntry(kind="SUBMIT", tick_at_event=0, text="hi")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-19: TranscriptEntry accepted str kind")

    # tick_at_event must be a non-negative int.
    try:
        TranscriptEntry(kind=TranscriptKind.SUBMIT, tick_at_event=-1, text="x")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-19: TranscriptEntry accepted negative tick_at_event"
        )
    try:
        TranscriptEntry(kind=TranscriptKind.SUBMIT, tick_at_event=True, text="x")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-UI-19: TranscriptEntry accepted bool tick_at_event"
        )

    # text must be a str.
    try:
        TranscriptEntry(kind=TranscriptKind.SUBMIT, tick_at_event=0, text=123)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-19: TranscriptEntry accepted non-str text")

    # Non-printable text is rejected.
    try:
        TranscriptEntry(
            kind=TranscriptKind.SUBMIT, tick_at_event=0, text="hello\x01world"
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-19: TranscriptEntry accepted non-printable text"
        )

    # Over-long text is truncated with an ellipsis suffix.
    long_text = "x" * (TRANSCRIPT_MAX_TEXT_LEN + 50)
    bounded = TranscriptEntry(
        kind=TranscriptKind.SUBMIT, tick_at_event=0, text=long_text
    )
    assert len(bounded.text) == TRANSCRIPT_MAX_TEXT_LEN, (
        f"I-UI-19: bounded text len must be {TRANSCRIPT_MAX_TEXT_LEN} "
        f"(got {len(bounded.text)})"
    )
    assert bounded.text.endswith("…"), (
        "I-UI-19: truncated transcript text must end with an ellipsis"
    )
    # The surviving prefix is still printable.
    assert bounded.text.isprintable(), (
        "I-UI-19: truncated transcript text must be printable"
    )

    # Empty text is allowed (a transcript entry with no payload body).
    bare = TranscriptEntry(kind=TranscriptKind.QUIT, tick_at_event=0, text="")
    assert bare.text == ""

    # ---- append is copy-on-write -----------------------------------------
    t0 = OperatorTranscript.empty()
    t1 = t0.append(TranscriptKind.SUBMIT, 0, "/help")
    # The original is unchanged.
    assert t0.entries == (), "I-UI-19: append mutated the source transcript"
    # The new value has exactly one entry.
    assert len(t1) == 1
    assert t1.entries[0].kind is TranscriptKind.SUBMIT
    assert t1.entries[0].tick_at_event == 0
    assert t1.entries[0].text == "/help"
    # The new value is a distinct object identity.
    assert t1 is not t0, "I-UI-19: copy-on-write must return a fresh transcript"
    # Repeated append keeps the original immutable.
    t2 = t1.append(TranscriptKind.VIEW, 0, "view = help")
    assert len(t0) == 0 and len(t1) == 1 and len(t2) == 2
    assert t2.entries[-1].text == "view = help"

    # last() reflects the newest entry.
    assert t2.last() is not None
    assert t2.last().kind is TranscriptKind.VIEW  # type: ignore[union-attr]

    # ---- extend() is also copy-on-write ----------------------------------
    t3 = t0.extend(
        (
            (TranscriptKind.SUBMIT, 0, "/queue beta hello"),
            (TranscriptKind.QUEUED, 0, "queued percept 'beta' (queue size = 1)"),
            (TranscriptKind.SUBMIT, 0, "/step"),
            (TranscriptKind.STEP, 1, "tick 1 ok (MODE_A)"),
        )
    )
    assert t0.entries == (), "I-UI-19: extend mutated the source transcript"
    assert len(t3) == 4
    assert [e.kind for e in t3.entries] == [
        TranscriptKind.SUBMIT,
        TranscriptKind.QUEUED,
        TranscriptKind.SUBMIT,
        TranscriptKind.STEP,
    ]
    assert t3.entries[-1].tick_at_event == 1

    # ---- Bounded ring (oldest dropped) -----------------------------------
    # Fill the ring to its limit and then add one more entry; the
    # resulting ring must hold exactly TRANSCRIPT_MAX_ENTRIES entries and
    # the oldest must have been dropped.
    items = tuple(
        (TranscriptKind.SUBMIT, i, f"line {i}")
        for i in range(TRANSCRIPT_MAX_ENTRIES + 3)
    )
    big = OperatorTranscript.empty().extend(items)
    assert len(big) == TRANSCRIPT_MAX_ENTRIES, (
        f"I-UI-19: ring must bound at {TRANSCRIPT_MAX_ENTRIES} "
        f"(got {len(big)})"
    )
    # The oldest surviving entry's text reflects the drop: we appended
    # TRANSCRIPT_MAX_ENTRIES + 3 entries, so the first three must have
    # been dropped (texts "line 0", "line 1", "line 2").
    assert big.entries[0].text == f"line 3", (
        f"I-UI-19: oldest entry should be 'line 3' "
        f"(got {big.entries[0].text!r})"
    )
    assert big.entries[-1].text == f"line {TRANSCRIPT_MAX_ENTRIES + 2}"

    # The bound limit cannot be exceeded by direct construction either.
    try:
        OperatorTranscript(
            entries=tuple(
                TranscriptEntry(
                    kind=TranscriptKind.SUBMIT, tick_at_event=i, text=f"x{i}"
                )
                for i in range(TRANSCRIPT_MAX_ENTRIES + 1)
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "I-UI-19: OperatorTranscript accepted entries beyond its limit"
        )

    # Custom limits are honored (used by fixtures to exercise the bound
    # without constructing 64+ entries).
    small = OperatorTranscript.empty(limit=3).extend(
        (
            (TranscriptKind.SUBMIT, 0, "a"),
            (TranscriptKind.SUBMIT, 0, "b"),
            (TranscriptKind.SUBMIT, 0, "c"),
            (TranscriptKind.SUBMIT, 0, "d"),
        )
    )
    assert len(small) == 3
    assert [e.text for e in small.entries] == ["b", "c", "d"], (
        f"I-UI-19: small ring drop order drifted ({[e.text for e in small.entries]!r})"
    )
    # limit must be a positive int.
    try:
        OperatorTranscript.empty(limit=0)
    except ValueError:
        pass
    else:
        raise AssertionError("I-UI-19: limit=0 was accepted")
    try:
        OperatorTranscript.empty(limit=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("I-UI-19: negative limit was accepted")
    try:
        OperatorTranscript(entries=(), limit=True)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-19: limit=True (bool) was accepted")

    # entries must be a tuple of TranscriptEntry values.
    try:
        OperatorTranscript(entries=["not a tuple"])  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("I-UI-19: entries as list was accepted")
    try:
        OperatorTranscript(entries=("not an entry",))  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "I-UI-19: entries containing a non-TranscriptEntry was accepted"
        )

    # ---- to_snapshot returns the read-only renderer projection -----------
    snap = t3.to_snapshot()
    assert isinstance(snap, TranscriptSnapshot)
    assert len(snap.entries) == len(t3.entries)
    for entry, projected in zip(t3.entries, snap.entries):
        assert isinstance(projected, TranscriptSnapshotEntry)
        # The kind is projected as a plain str (TranscriptKind's str value).
        assert projected.kind == entry.kind.value, (
            f"I-UI-19: snapshot kind drift "
            f"({projected.kind!r} vs {entry.kind.value!r})"
        )
        assert projected.tick_at_event == entry.tick_at_event
        assert projected.text == entry.text

    # Empty transcript projects to an empty snapshot.
    empty_snap = OperatorTranscript.empty().to_snapshot()
    assert isinstance(empty_snap, TranscriptSnapshot)
    assert empty_snap.entries == ()

    # ---- Resource-free: no callable / file handle / socket / LLM client.
    # The frozen dataclass slots already constrain the attribute surface;
    # we audit each declared field for any callable / unsafe shape.
    for entry in t3.entries:
        for attr in ("kind", "tick_at_event", "text"):
            value = getattr(entry, attr)
            assert not callable(value), (
                f"I-UI-19: TranscriptEntry.{attr} is callable ({value!r})"
            )
            assert not hasattr(value, "eval_consistency"), (
                f"I-UI-19: TranscriptEntry.{attr} looks like an LLM client"
            )
            assert not hasattr(value, "fileno"), (
                f"I-UI-19: TranscriptEntry.{attr} exposes fileno() "
                "(resource-like)"
            )
            assert not hasattr(value, "send_signal"), (
                f"I-UI-19: TranscriptEntry.{attr} looks like a subprocess handle"
            )

    # ---- Persistence audit (corrigenda ruling D) -------------------------
    # The transcript module must not perform filesystem I/O, open sockets,
    # spawn subprocesses, or import the trace / scenario / developmental
    # history modules. We re-check this with a small AST audit so a
    # future refactor cannot silently introduce a persistence path.
    transcript_path = (
        Path(__file__).resolve().parent.parent / "transcript.py"
    )
    assert transcript_path.exists(), (
        "I-UI-19: brain/ui/transcript.py is missing from the package"
    )
    tree = ast.parse(transcript_path.read_text(encoding="utf-8"))

    forbidden_modules: frozenset[str] = frozenset({
        "os",
        "io",
        "pathlib",
        "tempfile",
        "shutil",
        "shelve",
        "pickle",
        "json",
        "csv",
        "sqlite3",
        "socket",
        "subprocess",
        "urllib",
        "http",
        "requests",
        "curses",
        "brain.tick",
        "brain.tlica",
        "brain.llm",
        "brain.trace",
        "brain.development",
        "brain.development.output",
        "brain.development.worldlet",
        "brain.development.repl",
    })
    forbidden_attr_calls: frozenset[str] = frozenset({
        "open",
        "write",
        "writelines",
        "dump",
        "dumps",
        "send",
        "sendall",
        "connect",
        "system",
        "popen",
    })

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                root = name.split(".")[0]
                assert name not in forbidden_modules and root not in forbidden_modules or (
                    not (
                        name in forbidden_modules
                        or root in forbidden_modules
                    )
                ), None  # noqa: PT018
                if name in forbidden_modules or root in forbidden_modules:
                    raise AssertionError(
                        "I-UI-19 violated: brain/ui/transcript.py imports "
                        f"forbidden module {name!r}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0] if module else ""
            if module in forbidden_modules or root in forbidden_modules:
                raise AssertionError(
                    "I-UI-19 violated: brain/ui/transcript.py imports "
                    f"forbidden module {module!r}"
                )
        elif isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in {"open", "exec", "eval", "compile", "__import__"}:
                raise AssertionError(
                    "I-UI-19 violated: brain/ui/transcript.py calls "
                    f"forbidden builtin {name!r}"
                )
            if name in forbidden_attr_calls and isinstance(func, ast.Attribute):
                # Reject obvious resource-mutation patterns (file write,
                # socket send, os.system, etc.). We only flag attribute
                # forms so unrelated locals named "open" do not false-positive.
                raise AssertionError(
                    "I-UI-19 violated: brain/ui/transcript.py calls "
                    f"forbidden method {name!r}"
                )

    # ---- Determinism: same construction sequence yields equal transcripts.
    a = OperatorTranscript.empty().extend(
        (
            (TranscriptKind.SUBMIT, 0, "/help"),
            (TranscriptKind.VIEW, 0, "view = help"),
        )
    )
    b = OperatorTranscript.empty().extend(
        (
            (TranscriptKind.SUBMIT, 0, "/help"),
            (TranscriptKind.VIEW, 0, "view = help"),
        )
    )
    assert a.entries == b.entries, (
        "I-UI-19: identical construction produced different transcripts"
    )


__all__ = [
    "check_I_UI_19_transcript_is_local_copy_on_write",
]
