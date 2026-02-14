from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict

from interpreter import DSLError, Interpreter


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_assignment(text: str) -> tuple[str, Any]:
    if "=" not in text:
        raise ValueError("Expected NAME=VALUE")
    name, raw_value = text.split("=", 1)
    name = name.strip()
    raw_value = raw_value.strip()
    if not name or not _NAME_RE.match(name):
        raise ValueError(f"Invalid variable name: {name}")
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric value for {name}: {raw_value}") from exc
    return name, value


def _parse_assignments(items: list[str]) -> Dict[str, Any]:
    env: Dict[str, Any] = {}
    for item in items:
        name, value = _parse_assignment(item)
        env[name] = value
    return env


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run DSL scripts.")
    parser.add_argument("script", help="Path to .clc script")
    parser.add_argument("vars", nargs="*", help="Variable overrides: name=value")
    parser.add_argument("--trace", action="store_true", help="Enable trace mode for debugging")
    args = parser.parse_args(argv)

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"Script not found: {script_path}", file=sys.stderr)
        return 2

    try:
        overrides = _parse_assignments(args.vars)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    interpreter = Interpreter(initial_env=overrides, trace=args.trace)
    try:
        program = script_path.read_text(encoding="utf-8")
        result = interpreter.execute(program)
        if result is not None:
            print(interpreter.format_value(result))
    except DSLError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
