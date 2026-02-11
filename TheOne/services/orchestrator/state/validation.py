from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "packages" / "shared" / "schemas" / "canonical_state.schema.json"
)


class StateValidationError(ValueError):
    pass


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_state(state: dict[str, Any]) -> None:
    schema = _load_schema()
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - fallback for minimal env
        _manual_validate_root(state, schema)
        return

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(state), key=lambda e: e.path)
    if errors:
        messages = "; ".join(f"{list(err.path)}: {err.message}" for err in errors)
        raise StateValidationError(messages)


def _manual_validate_root(state: dict[str, Any], schema: dict[str, Any]) -> None:
    if not isinstance(state, dict):
        raise StateValidationError("state must be an object")
    required = set(schema.get("required", []))
    keys = set(state.keys())
    missing = sorted(required - keys)
    unknown = sorted(keys - set(schema.get("properties", {}).keys()))
    if missing:
        raise StateValidationError(f"missing required keys: {missing}")
    if unknown:
        raise StateValidationError(f"unknown root keys: {unknown}")
