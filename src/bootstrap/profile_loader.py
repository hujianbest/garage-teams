"""Runtime-home profile loader and authority resolution helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from foundation import RuntimeHomeBinding, RuntimeProfile


class RuntimeProfileResolutionError(RuntimeError):
    """Raised when runtime-home profile authority cannot be resolved safely."""


def load_runtime_profile(
    runtime_home: RuntimeHomeBinding,
    *,
    profile_id: str,
    runtime_capabilities: tuple[str, ...] = (),
    provider_hints: Mapping[str, str] | None = None,
) -> RuntimeProfile:
    hints = dict(provider_hints or {})
    _reject_authority_overrides(hints)

    profile_mapping, profile_source = _read_optional_json(runtime_home.profiles_root / f"{profile_id}.json")
    config_mapping, config_source = _read_optional_json(runtime_home.config_root / "providers.json")

    defaults = _mapping_from(config_mapping, "defaults", default={})
    profile_overrides = _mapping_from(
        _mapping_from(config_mapping, "profiles", default={}),
        profile_id,
        default={},
    )

    provider_id = _first_non_empty(
        _string_from(profile_mapping, "providerId"),
        _string_from(profile_overrides, "providerId"),
        _string_from(defaults, "providerId"),
    )
    model_id = _first_non_empty(
        _string_from(profile_mapping, "modelId"),
        _string_from(profile_overrides, "modelId"),
        _string_from(defaults, "modelId"),
    )
    adapter_id = _first_non_empty(
        _string_from(profile_mapping, "adapterId"),
        _string_from(profile_overrides, "adapterId"),
        _string_from(defaults, "adapterId"),
    )

    adapter_settings: Mapping[str, str] = {}
    adapter_source: str | None = None
    if adapter_id is not None:
        adapter_settings, adapter_source = _read_optional_json(runtime_home.adapters_root / f"{adapter_id}.json")
        _validate_adapter_authority(adapter_settings, provider_id=provider_id, model_id=model_id, adapter_id=adapter_id)

    capabilities = _merge_capabilities(
        runtime_capabilities,
        _tuple_from(profile_mapping, "capabilities"),
        _tuple_from(profile_overrides, "capabilities"),
        _tuple_from(defaults, "capabilities"),
    )
    authority_sources = tuple(
        source
        for source in (profile_source, config_source, adapter_source)
        if source is not None
    )

    return RuntimeProfile(
        profile_id=profile_id,
        runtime_home=runtime_home.root,
        capabilities=capabilities,
        provider_id=provider_id,
        model_id=model_id,
        adapter_id=adapter_id,
        provider_hints=hints,
        adapter_settings={key: value for key, value in adapter_settings.items() if isinstance(value, str)},
        authority_sources=authority_sources,
    )


def _read_optional_json(path: Path) -> tuple[Mapping[str, Any], str | None]:
    if not path.exists():
        return {}, None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeProfileResolutionError(f"Expected mapping content in {path}.")
    return raw, str(path)


def _mapping_from(raw: Mapping[str, Any], key: str, *, default: Mapping[str, Any]) -> Mapping[str, Any]:
    value = raw.get(key, default)
    if value is None:
        return default
    if not isinstance(value, dict):
        raise RuntimeProfileResolutionError(f"Expected {key!r} to be a mapping.")
    return value


def _string_from(raw: Mapping[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RuntimeProfileResolutionError(f"Expected {key!r} to be a non-empty string when provided.")
    return value.strip()


def _tuple_from(raw: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = raw.get(key, ())
    if value in (None, ()):
        return ()
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, list):
        values = tuple(value)
    else:
        raise RuntimeProfileResolutionError(f"Expected {key!r} to be a string or list of strings.")
    normalized: list[str] = []
    for item in values:
        if not isinstance(item, str) or not item.strip():
            raise RuntimeProfileResolutionError(f"Expected {key!r} items to be non-empty strings.")
        normalized.append(item.strip())
    return tuple(normalized)


def _merge_capabilities(*capability_sets: tuple[str, ...]) -> tuple[str, ...]:
    merged: list[str] = []
    for capability_set in capability_sets:
        for capability in capability_set:
            if capability not in merged:
                merged.append(capability)
    return tuple(merged)


def _reject_authority_overrides(provider_hints: Mapping[str, str]) -> None:
    authority_keys = {"providerId", "modelId", "adapterId"}
    illegal = sorted(authority_keys & set(provider_hints))
    if illegal:
        raise RuntimeProfileResolutionError(
            f"Provider hints cannot override runtime authority fields: {illegal}."
        )


def _validate_adapter_authority(
    adapter_settings: Mapping[str, Any],
    *,
    provider_id: str | None,
    model_id: str | None,
    adapter_id: str,
) -> None:
    adapter_provider = _string_from(adapter_settings, "providerId")
    adapter_model = _string_from(adapter_settings, "modelId")
    if adapter_provider is not None and provider_id is not None and adapter_provider != provider_id:
        raise RuntimeProfileResolutionError(
            f"Adapter {adapter_id!r} conflicts with resolved provider authority {provider_id!r}."
        )
    if adapter_model is not None and model_id is not None and adapter_model != model_id:
        raise RuntimeProfileResolutionError(
            f"Adapter {adapter_id!r} conflicts with resolved model authority {model_id!r}."
        )


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is not None:
            return value
    return None
