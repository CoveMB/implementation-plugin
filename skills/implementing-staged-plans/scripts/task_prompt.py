#!/usr/bin/env python3
"""Render and validate one byte-exact implementation task prompt envelope."""

from __future__ import annotations

import json
from collections.abc import Mapping


PROMPT_ENVELOPE_SCHEMA = "implementation-exact-prompt-envelope/v1"
SKILL_INVOCATION = "$implementing-staged-plans"
SELF_DIGEST_FIELDS = frozenset({"prompt_sha256", "submitted_prompt_sha256"})


def _contains_self_digest(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key in SELF_DIGEST_FIELDS or _contains_self_digest(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_self_digest(item) for item in value)
    return False


def _canonical_json(value: Mapping[str, object]) -> str:
    try:
        return json.dumps(
            dict(value),
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"exact prompt command is not canonical JSON: {error}") from error


def render_exact_prompt(command: Mapping[str, object]) -> str:
    """Render one exact skill invocation and canonical JSON command."""
    if not isinstance(command, Mapping):
        raise ValueError("exact prompt command must be a mapping")
    materialized = dict(command)
    schema = materialized.get("schema_version")
    if not isinstance(schema, str) or not schema:
        raise ValueError("exact prompt command schema_version is required")
    if _contains_self_digest(materialized):
        raise ValueError("exact prompt command must not contain a self-digest field")
    payload = _canonical_json(materialized)
    return f"{SKILL_INVOCATION}\n\n```json\n{payload}\n```\n"


def parse_exact_prompt(markdown: str, expected_schema: str) -> dict[str, object]:
    """Parse only a byte-identical prompt rendered for the expected schema."""
    if not isinstance(markdown, str):
        raise ValueError("exact prompt must be submitted directly as text")
    prefix = f"{SKILL_INVOCATION}\n\n```json\n"
    suffix = "\n```\n"
    if not markdown.startswith(prefix) or not markdown.endswith(suffix):
        raise ValueError("exact prompt transport does not match the required envelope")
    payload = markdown[len(prefix) : -len(suffix)]
    try:
        command = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError(f"exact prompt contains invalid JSON: {error.msg}") from error
    if not isinstance(command, dict):
        raise ValueError("exact prompt command must be a JSON object")
    if command.get("schema_version") != expected_schema:
        raise ValueError(
            f"exact prompt schema mismatch: expected {expected_schema!r}"
        )
    if render_exact_prompt(command) != markdown:
        raise ValueError("exact prompt bytes are not canonical")
    return command
