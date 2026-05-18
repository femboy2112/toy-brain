#!/usr/bin/env python3
"""Selftest for flow_manifest.py.

This file intentionally disables bytecode writes before loading the helper so a
plain `python3 tools/claude_helpers/flow_manifest_selftest.py` run does not
leave __pycache__ artifacts in the repository.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile


sys.dont_write_bytecode = True


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "flow_manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("flow_manifest_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load spec for {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


flow_manifest = load_module()


def tiny_manifest(nodes, task="test task"):
    return {"task": task, "nodes": nodes}


def node(node_id, allowed=None, **extra):
    data = {
        "id": node_id,
        "prompt": f"do {node_id}",
        "allowed_files": allowed if allowed is not None else [f"out/{node_id}.txt"],
    }
    data.update(extra)
    return data


def write_manifest(tmp, manifest):
    path = Path(tmp) / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return str(path)


def run_main(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = flow_manifest.main(argv)
    return code, out.getvalue(), err.getvalue()


def validate_json(tmp, manifest, extra=None):
    path = write_manifest(tmp, manifest)
    argv = ["validate", path, "--json"]
    if extra:
        argv.extend(extra)
    code, out, err = run_main(argv)
    try:
        payload = json.loads(out)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"validate did not emit JSON: code={code} stdout={out!r} stderr={err!r}") from exc
    return code, payload, out, err


def rules(payload, key="errors"):
    return {item["rule"] for item in payload[key]}


def assert_rule(payload, rule, key="errors"):
    present = rules(payload, key)
    assert rule in present, f"expected {rule!r} in {key}, got {present!r}; payload={payload!r}"


def test_good_minimal(tmp):
    manifest = tiny_manifest([node("a", ["src/a.py"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 0
    assert payload["valid"] is True
    assert payload["errors"] == []
    assert payload["warnings"] == []


def test_good_two_independent(tmp):
    manifest = tiny_manifest([node("a", ["src/a.py"]), node("b", ["src/b.py"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 0
    assert payload["valid"] is True


def test_good_chained(tmp):
    manifest = tiny_manifest([node("a", ["src/shared.py"]), node("b", ["src/shared.py"], depends_on=["a"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 0
    assert payload["valid"] is True


def test_cycle(tmp):
    manifest = tiny_manifest([node("a", depends_on=["b"]), node("b", depends_on=["a"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 1
    assert_rule(payload, "cycle")


def test_self_dependency(tmp):
    manifest = tiny_manifest([node("a", depends_on=["a"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 1
    assert_rule(payload, "self-dependency")


def test_write_write_no_dep(tmp):
    manifest = tiny_manifest([node("a", ["src/shared.py"]), node("b", ["src/shared.py"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 1
    assert_rule(payload, "write/write-no-dependency")


def test_missing_dep_target(tmp):
    manifest = tiny_manifest([node("a", depends_on=["ghost"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 1
    assert_rule(payload, "missing-dependency-target")


def test_allow_delete_not_allowed(tmp):
    manifest = tiny_manifest([node("a", ["src/a.py"], allow_delete=["src/other.py"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 1
    assert_rule(payload, "allow_delete-not-allowed")


def test_invalid_path(tmp):
    manifest = tiny_manifest([node("a", ["../x.py", "/abs.py", "has\\backslash.py"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 1
    assert_rule(payload, "invalid-path")


def test_cap_exceeded(tmp):
    manifest = tiny_manifest([node(f"n{i}") for i in range(5)])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 1
    assert_rule(payload, "cap-exceeded")
    code2, payload2, _out2, _err2 = validate_json(tmp, manifest, ["--operator-approved-over-three-calls"])
    assert code2 == 0
    assert payload2["valid"] is True


def test_max_parallel_too_high(tmp):
    manifest = tiny_manifest([node("a")])
    code, payload, _out, _err = validate_json(tmp, manifest, ["--max-parallel", "3"])
    assert code == 1
    assert_rule(payload, "cap-exceeded")


def test_read_write_collision_warning(tmp):
    manifest = tiny_manifest([node("a", ["src/a.py"], read_files=["src/b.py"]), node("b", ["src/b.py"])])
    code, payload, _out, _err = validate_json(tmp, manifest)
    assert code == 0
    assert payload["valid"] is True
    assert_rule(payload, "read/write-no-dependency", key="warnings")
    code2, payload2, _out2, _err2 = validate_json(tmp, manifest, ["--strict"])
    assert code2 == 1
    assert payload2["valid"] is False
    assert_rule(payload2, "read/write-no-dependency", key="warnings")


def test_scaffold_round_trip(tmp):
    out_path = str(Path(tmp) / "scaffold.json")
    code, out, err = run_main(["scaffold", "--out", out_path])
    assert code == 0, f"scaffold failed stdout={out!r} stderr={err!r}"
    code2, payload, _out2, _err2 = validate_json(tmp, json.loads(Path(out_path).read_text(encoding="utf-8")))
    assert code2 == 0
    assert payload["valid"] is True


def test_summary_runs(tmp):
    manifest = tiny_manifest([node("a")], task="summary task")
    path = write_manifest(tmp, manifest)
    code, out, err = run_main(["summary", path])
    assert code == 0, f"summary failed stdout={out!r} stderr={err!r}"
    assert "Task: summary task" in out


def test_malformed_json(tmp):
    path = Path(tmp) / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    code, out, _err = run_main(["validate", str(path), "--json"])
    assert code == 2
    payload = json.loads(out)
    assert_rule(payload, "json-error")


def test_missing_file(tmp):
    path = Path(tmp) / "missing.json"
    code, out, _err = run_main(["validate", str(path), "--json"])
    assert code == 2
    payload = json.loads(out)
    assert_rule(payload, "file-error")


def main() -> int:
    tests = [
        test_good_minimal,
        test_good_two_independent,
        test_good_chained,
        test_cycle,
        test_self_dependency,
        test_write_write_no_dep,
        test_missing_dep_target,
        test_allow_delete_not_allowed,
        test_invalid_path,
        test_cap_exceeded,
        test_max_parallel_too_high,
        test_read_write_collision_warning,
        test_scaffold_round_trip,
        test_summary_runs,
        test_malformed_json,
        test_missing_file,
    ]
    for test in tests:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                test(tmp)
            except Exception as exc:
                print(f"flow_manifest_selftest: FAIL {test.__name__}: {exc}", file=sys.stderr)
                return 1
    print("flow_manifest_selftest: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
