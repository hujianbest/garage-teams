"""Session lifecycle state machine helpers."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "BlockedGateError",
    "InvalidSessionTransitionError",
    "SessionAction",
    "SessionController",
    "TransitionOutcome",
    "describe_transition",
    "required_record_types_for_action",
]


def __getattr__(name: str) -> object:
    if name in {"BlockedGateError", "SessionController", "TransitionOutcome"}:
        module = import_module(".control", __name__)
        return getattr(module, name)
    if name in {
        "InvalidSessionTransitionError",
        "SessionAction",
        "describe_transition",
        "required_record_types_for_action",
    }:
        module = import_module(".lifecycle", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
