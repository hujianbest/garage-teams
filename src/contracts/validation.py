"""Validation helpers for shared contract loading."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .models import SUPPORTED_CONTRACT_VERSION


class ContractValidationError(ValueError):
    """Raised when a parsed contract violates runtime validation rules."""


def validate_contract_version(contract_version: str) -> None:
    if contract_version != SUPPORTED_CONTRACT_VERSION:
        raise ContractValidationError(
            f"Unsupported contractVersion {contract_version!r}; "
            f"expected {SUPPORTED_CONTRACT_VERSION!r}."
        )


def validate_extensions(
    extensions: Mapping[str, Any],
    *,
    allowed_extension_keys: Iterable[str] = (),
) -> None:
    if not extensions:
        return
    allowed = set(allowed_extension_keys)
    unknown = sorted(key for key in extensions if key not in allowed)
    if unknown:
        raise ContractValidationError(
            "Found unsupported extension fields: " + ", ".join(unknown)
        )
