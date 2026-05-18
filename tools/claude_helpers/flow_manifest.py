#!/usr/bin/env python3
"""Offline preflight helper for Stage C.1 Claude-supervised Codex manifests.

Subcommands: validate <path> [--json] [--strict] [caps], summary <path>, and
scaffold [--nodes N] [--out PATH]. Validation checks manifest shape, node fields,
relative POSIX paths, delete subsets, dependency references and cycles,
write/write conflicts, read/write sibling warnings, and Stage C.1 call caps.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import sys


EFFORT_VALUES = {"low", "medium", "high"}
DEFAULT_MAX_PARALLEL = 2
DEFAULT_MAX_TOTAL_CALLS = 3
OPERATOR_APPROVED_MAX_TOTAL_CALLS = 8
MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]+$")
NODE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class Issue:
    rule: str
    nodes: tuple[str, ...]
    detail: str

    def as_json(self) -> dict[str, object]:
        return {"rule": self.rule, "nodes": list(self.nodes), "detail": self.detail}


@dataclass(frozen=True)
class Node:
    node_id: str
    prompt: str
    allowed_files: tuple[str, ...]
    read_files: tuple[str, ...] = ()
    allow_delete: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    model: str | None = None
    effort: str | None = None
    timeout: int | None = None
    kind: str = "write"


@dataclass
class ValidationResult:
    valid: bool
    errors: list[Issue]
    warnings: list[Issue]
    stats: dict[str, int]
    task: str = ""
    nodes: list[Node] | None = None
    children: dict[str, list[str]] | None = None
    closure: dict[str, set[str]] | None = None

    def as_json(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "errors": [issue.as_json() for issue in self.errors],
            "warnings": [issue.as_json() for issue in self.warnings],
            "stats": self.stats,
        }


def _issue(rule: str, nodes: tuple[str, ...] | list[str] | str, detail: str) -> Issue:
    if isinstance(nodes, str):
        node_tuple = (nodes,)
    else:
        node_tuple = tuple(nodes)
    return Issue(rule=rule, nodes=node_tuple, detail=detail)


def load_json_file(path_text: str) -> tuple[object | None, str | None, str | None]:
    path = Path(path_text)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, "file-error", f"{path_text}: {exc}"
    try:
        return json.loads(text), None, None
    except json.JSONDecodeError as exc:
        return None, "json-error", f"{path_text}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"


def path_error(path: object, *, label: str) -> str | None:
    if not isinstance(path, str) or not path.strip():
        return f"{label} must be a non-empty string"
    if "\\" in path:
        return f"{label} contains a backslash: {path!r}"
    if path.startswith("/"):
        return f"{label} must be relative: {path!r}"
    pure = PurePosixPath(path)
    parts = pure.parts
    if not parts or str(pure) in {"", "."}:
        return f"{label} is not a file path: {path!r}"
    if any(part in {"", ".", ".."} for part in parts):
        return f"{label} contains '.', '..', or an empty path segment: {path!r}"
    if parts[0] == ".git":
        return f"{label} may not target .git: {path!r}"
    if path.endswith("/"):
        return f"{label} must not end with '/': {path!r}"
    return None


def normalize_path(path: object) -> str:
    return PurePosixPath(str(path)).as_posix()


def _as_string_array(value: object, *, node_id: str, field: str, errors: list[Issue]) -> list[object]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(_issue("invalid-field", node_id, f"{field} must be an array"))
        return []
    return value


def parse_nodes(manifest: dict[str, object], errors: list[Issue]) -> tuple[str, list[Node]]:
    task_raw = manifest.get("task")
    task = task_raw.strip() if isinstance(task_raw, str) else ""
    if not task:
        errors.append(_issue("manifest-shape", (), "manifest.task must be a non-empty string"))

    defaults = manifest.get("defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        errors.append(_issue("manifest-shape", (), "manifest.defaults must be an object if present"))
        defaults = {}

    default_model = defaults.get("model")
    default_effort = defaults.get("effort")
    default_timeout = defaults.get("timeout")
    if default_model is not None and not isinstance(default_model, str):
        errors.append(_issue("invalid-field", (), "defaults.model must be a string"))
    if default_effort is not None and default_effort not in EFFORT_VALUES:
        errors.append(_issue("invalid-field", (), "defaults.effort must be one of low, medium, high"))
    if default_timeout is not None and (not isinstance(default_timeout, int) or default_timeout <= 0):
        errors.append(_issue("invalid-field", (), "defaults.timeout must be a positive int"))

    raw_nodes = manifest.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        errors.append(_issue("manifest-shape", (), "manifest.nodes must be a non-empty array"))
        return task, []

    nodes: list[Node] = []
    seen: set[str] = set()
    for idx, raw in enumerate(raw_nodes):
        pseudo_id = f"#{idx}"
        if not isinstance(raw, dict):
            errors.append(_issue("node-shape", pseudo_id, "node must be an object"))
            continue

        node_id_raw = raw.get("id")
        if not isinstance(node_id_raw, str) or not node_id_raw.strip():
            errors.append(_issue("node-shape", pseudo_id, "node.id must be a non-empty string"))
            node_id = pseudo_id
        else:
            node_id = node_id_raw.strip()
            if node_id in seen:
                errors.append(_issue("duplicate-node-id", node_id, f"duplicate node id {node_id!r}"))
            seen.add(node_id)
            if not NODE_ID_RE.match(node_id):
                errors.append(_issue("invalid-field", node_id, "node.id contains unsupported characters"))

        prompt = raw.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(_issue("node-shape", node_id, "node.prompt must be a non-empty string"))
            prompt_text = ""
        else:
            prompt_text = prompt

        allowed_raw = raw.get("allowed_files")
        allowed_items: list[object]
        if not isinstance(allowed_raw, list) or not allowed_raw:
            errors.append(_issue("node-shape", node_id, "node.allowed_files must be a non-empty array"))
            allowed_items = []
        else:
            allowed_items = allowed_raw
        allowed: list[str] = []
        for path in allowed_items:
            err = path_error(path, label="allowed_files")
            if err:
                errors.append(_issue("invalid-path", node_id, err))
            else:
                allowed.append(normalize_path(path))

        reads: list[str] = []
        for path in _as_string_array(raw.get("read_files", []), node_id=node_id, field="read_files", errors=errors):
            err = path_error(path, label="read_files")
            if err:
                errors.append(_issue("invalid-path", node_id, err))
            else:
                reads.append(normalize_path(path))

        deletes: list[str] = []
        for path in _as_string_array(raw.get("allow_delete", []), node_id=node_id, field="allow_delete", errors=errors):
            err = path_error(path, label="allow_delete")
            if err:
                errors.append(_issue("invalid-path", node_id, err))
            else:
                deletes.append(normalize_path(path))
        for path in sorted(set(deletes) - set(allowed)):
            errors.append(_issue("allow_delete-not-allowed", node_id, f"{path} is not listed in allowed_files"))

        deps: list[str] = []
        for dep in _as_string_array(raw.get("depends_on", []), node_id=node_id, field="depends_on", errors=errors):
            if not isinstance(dep, str) or not dep.strip():
                errors.append(_issue("invalid-field", node_id, "depends_on entries must be non-empty strings"))
            else:
                deps.append(dep.strip())

        model = raw.get("model", default_model)
        if model is not None:
            if not isinstance(model, str) or not model.strip():
                errors.append(_issue("invalid-field", node_id, "model must be a non-empty string"))
                model = None
            elif not MODEL_RE.match(model):
                errors.append(_issue("invalid-field", node_id, "model contains unsupported characters"))

        effort = raw.get("effort", default_effort)
        if effort is not None and effort not in EFFORT_VALUES:
            errors.append(_issue("invalid-field", node_id, "effort must be one of low, medium, high"))
            effort = None

        timeout = raw.get("timeout", default_timeout)
        if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
            errors.append(_issue("invalid-field", node_id, "timeout must be a positive int"))
            timeout = None

        kind = raw.get("kind", "write")
        if kind != "write":
            errors.append(_issue("invalid-field", node_id, "kind must be 'write' if present"))
            kind = "write"

        nodes.append(
            Node(
                node_id=node_id,
                prompt=prompt_text,
                allowed_files=tuple(allowed),
                read_files=tuple(reads),
                allow_delete=tuple(deletes),
                depends_on=tuple(deps),
                model=model if isinstance(model, str) else None,
                effort=effort if isinstance(effort, str) else None,
                timeout=timeout if isinstance(timeout, int) else None,
                kind=kind,
            )
        )
    return task, nodes


def dependency_graph(nodes: list[Node], errors: list[Issue]) -> tuple[dict[str, Node], dict[str, list[str]]]:
    node_by_id = {node.node_id: node for node in nodes}
    children: dict[str, list[str]] = {node.node_id: [] for node in nodes}
    for node in nodes:
        for dep in node.depends_on:
            if dep == node.node_id:
                errors.append(_issue("self-dependency", node.node_id, f"{node.node_id} depends on itself"))
                continue
            if dep not in node_by_id:
                errors.append(_issue("missing-dependency-target", node.node_id, f"{node.node_id} depends on unknown node {dep!r}"))
                continue
            children[dep].append(node.node_id)
    for child_list in children.values():
        child_list.sort()
    return node_by_id, children


def find_cycle(nodes: list[Node], node_by_id: dict[str, Node]) -> list[str] | None:
    color: dict[str, int] = {node.node_id: 0 for node in nodes}
    stack: list[str] = []
    stack_index: dict[str, int] = {}

    def dfs(node_id: str) -> list[str] | None:
        color[node_id] = 1
        stack_index[node_id] = len(stack)
        stack.append(node_id)
        for dep in node_by_id[node_id].depends_on:
            if dep == node_id or dep not in node_by_id:
                continue
            if color.get(dep, 0) == 0:
                found = dfs(dep)
                if found:
                    return found
            elif color.get(dep) == 1:
                return stack[stack_index[dep] :] + [dep]
        stack.pop()
        stack_index.pop(node_id, None)
        color[node_id] = 2
        return None

    for node in nodes:
        if color[node.node_id] == 0:
            found = dfs(node.node_id)
            if found:
                return found
    return None


def transitive_closure(nodes: list[Node], node_by_id: dict[str, Node]) -> dict[str, set[str]]:
    closure: dict[str, set[str]] = {}

    def walk(node_id: str, seen: set[str]) -> set[str]:
        if node_id in closure:
            return set(closure[node_id])
        deps_total: set[str] = set()
        for dep in node_by_id[node_id].depends_on:
            if dep == node_id or dep not in node_by_id or dep in seen:
                continue
            deps_total.add(dep)
            deps_total.update(walk(dep, seen | {dep}))
        closure[node_id] = deps_total
        return set(deps_total)

    for node in nodes:
        walk(node.node_id, {node.node_id})
    return closure


def max_depth(nodes: list[Node], node_by_id: dict[str, Node]) -> int:
    memo: dict[str, int] = {}

    def depth(node_id: str, seen: set[str]) -> int:
        if node_id in memo:
            return memo[node_id]
        best = 0
        for dep in node_by_id[node_id].depends_on:
            if dep == node_id or dep not in node_by_id or dep in seen:
                continue
            best = max(best, 1 + depth(dep, seen | {dep}))
        memo[node_id] = best
        return best

    return max((depth(node.node_id, {node.node_id}) for node in nodes), default=0)


def validate_relations(nodes: list[Node], closure: dict[str, set[str]], errors: list[Issue], warnings: list[Issue]) -> None:
    for idx, a in enumerate(nodes):
        for b in nodes[idx + 1 :]:
            a_dep_b = b.node_id in closure.get(a.node_id, set())
            b_dep_a = a.node_id in closure.get(b.node_id, set())
            related = a_dep_b or b_dep_a
            write_overlap = sorted(set(a.allowed_files) & set(b.allowed_files))
            if write_overlap and not related:
                errors.append(
                    _issue(
                        "write/write-no-dependency",
                        (a.node_id, b.node_id),
                        f"overlap: {', '.join(write_overlap)}",
                    )
                )
            rw_a = sorted(set(a.read_files) & set(b.allowed_files))
            rw_b = sorted(set(b.read_files) & set(a.allowed_files))
            if not related and (rw_a or rw_b):
                paths = sorted(set(rw_a) | set(rw_b))
                warnings.append(
                    _issue(
                        "read/write-no-dependency",
                        (a.node_id, b.node_id),
                        f"overlap: {', '.join(paths)}",
                    )
                )


def validate_caps(
    nodes: list[Node],
    *,
    max_parallel: int,
    max_total_calls: int,
    operator_approved: bool,
    errors: list[Issue],
) -> None:
    if max_parallel < 1:
        errors.append(_issue("cap-exceeded", (), "max_parallel must be at least 1"))
    if max_parallel > DEFAULT_MAX_PARALLEL:
        errors.append(_issue("cap-exceeded", (), "max_parallel above 2 is not allowed"))
    if max_total_calls < 1:
        errors.append(_issue("cap-exceeded", (), "max_total_calls must be at least 1"))
    if max_total_calls > DEFAULT_MAX_TOTAL_CALLS and not operator_approved:
        errors.append(_issue("cap-exceeded", (), "max_total_calls above 3 requires operator approval"))
    if operator_approved:
        if len(nodes) > OPERATOR_APPROVED_MAX_TOTAL_CALLS:
            errors.append(_issue("cap-exceeded", (), "operator approval supports at most 8 nodes"))
        if max_total_calls > OPERATOR_APPROVED_MAX_TOTAL_CALLS:
            errors.append(_issue("cap-exceeded", (), "max_total_calls above 8 is not supported"))
    elif len(nodes) > max_total_calls:
        errors.append(_issue("cap-exceeded", (), f"manifest has {len(nodes)} nodes but max_total_calls={max_total_calls}"))


def validate_manifest(
    manifest: object,
    *,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
    max_total_calls: int = DEFAULT_MAX_TOTAL_CALLS,
    operator_approved: bool = False,
    strict: bool = False,
) -> ValidationResult:
    errors: list[Issue] = []
    warnings: list[Issue] = []
    if not isinstance(manifest, dict):
        errors.append(_issue("manifest-shape", (), "manifest must be a JSON object"))
        return ValidationResult(False, errors, warnings, {"node_count": 0, "max_dependency_depth": 0, "isolated_node_count": 0})

    task, nodes = parse_nodes(manifest, errors)
    node_by_id, children = dependency_graph(nodes, errors)
    cycle = find_cycle(nodes, node_by_id)
    if cycle:
        errors.append(_issue("cycle", tuple(dict.fromkeys(cycle)), "dependency cycle: " + " -> ".join(cycle)))
    closure = transitive_closure(nodes, node_by_id)
    validate_relations(nodes, closure, errors, warnings)
    validate_caps(nodes, max_parallel=max_parallel, max_total_calls=max_total_calls, operator_approved=operator_approved, errors=errors)

    depended_on = {child for values in children.values() for child in values}
    isolated = [node.node_id for node in nodes if not node.depends_on and node.node_id not in depended_on]
    stats = {
        "node_count": len(nodes),
        "max_dependency_depth": max_depth(nodes, node_by_id),
        "isolated_node_count": len(isolated),
    }
    valid = not errors and not (strict and warnings)
    return ValidationResult(valid, errors, warnings, stats, task=task, nodes=nodes, children=children, closure=closure)


def print_text_validation(result: ValidationResult, *, strict: bool) -> None:
    print("Errors")
    if result.errors:
        for issue in result.errors:
            nodes = ", ".join(issue.nodes) if issue.nodes else "<manifest>"
            print(f"- {issue.rule} [{nodes}]: {issue.detail}")
    elif strict and result.warnings:
        print("- <none>; warnings are fatal because --strict was passed")
    else:
        print("- <none>")

    print()
    print("Warnings")
    if result.warnings:
        for issue in result.warnings:
            nodes = ", ".join(issue.nodes) if issue.nodes else "<manifest>"
            print(f"- {issue.rule} [{nodes}]: {issue.detail}")
    else:
        print("- <none>")

    print()
    print("OK")
    if result.valid:
        print(f"- manifest is valid ({result.stats['node_count']} node(s))")
    else:
        print("- manifest is not valid")
    print(f"- max_dependency_depth: {result.stats['max_dependency_depth']}")
    print(f"- isolated_node_count: {result.stats['isolated_node_count']}")


def command_validate(args: argparse.Namespace) -> int:
    manifest, err_kind, err_detail = load_json_file(args.path)
    if err_kind:
        if args.json:
            print(json.dumps({"valid": False, "errors": [{"rule": err_kind, "nodes": [], "detail": err_detail}], "warnings": [], "stats": {"node_count": 0, "max_dependency_depth": 0, "isolated_node_count": 0}}, indent=2, sort_keys=True))
        else:
            print(f"Error: {err_detail}", file=sys.stderr)
        return 2
    result = validate_manifest(
        manifest,
        max_parallel=args.max_parallel,
        max_total_calls=args.max_total_calls,
        operator_approved=args.operator_approved_over_three_calls,
        strict=args.strict,
    )
    if args.json:
        print(json.dumps(result.as_json(), indent=2, sort_keys=True))
    else:
        print_text_validation(result, strict=args.strict)
    if result.errors or (args.strict and result.warnings):
        return 1
    return 0


def command_summary(args: argparse.Namespace) -> int:
    manifest, err_kind, err_detail = load_json_file(args.path)
    if err_kind:
        print(f"Error: {err_detail}", file=sys.stderr)
        return 2
    result = validate_manifest(manifest, operator_approved=True)
    nodes = result.nodes or []
    children = result.children or {}
    depended_on = {child for values in children.values() for child in values}
    isolated = [node for node in nodes if not node.depends_on and node.node_id not in depended_on]
    chained = [node for node in nodes if node not in isolated]

    print(f"Task: {result.task or '<invalid>'}")
    print()
    print("Isolated")
    for node in isolated:
        print_node_block(node)
    if not isolated:
        print("- <none>")

    print()
    print("Chained")
    for node in chained:
        print_node_block(node)
    if not chained:
        print("- <none>")

    print()
    print("Dependency graph")
    printed = False
    for parent in sorted(children):
        if children[parent]:
            print(f"- {parent} -> {', '.join(children[parent])}")
            printed = True
    if not printed:
        print("- <none>")
    return 0


def print_node_block(node: Node) -> None:
    model = node.model or "<default>"
    effort = node.effort or "<default>"
    deps = ", ".join(node.depends_on) if node.depends_on else "<none>"
    print(f"- id: {node.node_id}")
    print(f"  model: {model}")
    print(f"  effort: {effort}")
    print(f"  allowed_files: {', '.join(node.allowed_files) if node.allowed_files else '<none>'}")
    print(f"  depends_on: {deps}")


def node_name(index: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    return f"node_{alphabet[index]}" if index < len(alphabet) else f"node_{index + 1}"


def scaffold_manifest(count: int) -> dict[str, object]:
    nodes: list[dict[str, object]] = []
    for idx in range(count):
        name = node_name(idx)
        nodes.append({"id": name, "prompt": "TODO: describe the node task", "allowed_files": [f"TODO/{name}.py"]})
    return {"task": "TODO: describe the flow task", "defaults": {}, "nodes": nodes}


def command_scaffold(args: argparse.Namespace) -> int:
    if args.nodes < 1:
        print("Error: --nodes must be at least 1", file=sys.stderr)
        return 2
    if args.nodes > OPERATOR_APPROVED_MAX_TOTAL_CALLS:
        print("Error: --nodes may not exceed 8", file=sys.stderr)
        return 2
    data = scaffold_manifest(args.nodes)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if args.out:
        try:
            Path(args.out).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"Error: {args.out}: {exc}", file=sys.stderr)
            return 2
    else:
        print(text, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight and scaffold Stage C.1 dynamic flow manifests.")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a manifest without running Codex")
    validate.add_argument("path")
    validate.add_argument("--json", action="store_true", help="Emit machine-readable validation result")
    validate.add_argument("--strict", action="store_true", help="Treat warnings as validation failures")
    validate.add_argument("--max-parallel", type=int, default=DEFAULT_MAX_PARALLEL)
    validate.add_argument("--max-total-calls", type=int, default=DEFAULT_MAX_TOTAL_CALLS)
    validate.add_argument("--operator-approved-over-three-calls", action="store_true")
    validate.set_defaults(func=command_validate)

    summary = sub.add_parser("summary", help="Pretty-print task, nodes, and dependency graph")
    summary.add_argument("path")
    summary.set_defaults(func=command_summary)

    scaffold = sub.add_parser("scaffold", help="Emit a minimal valid manifest skeleton")
    scaffold.add_argument("--nodes", type=int, default=2)
    scaffold.add_argument("--out")
    scaffold.set_defaults(func=command_scaffold)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
