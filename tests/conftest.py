"""Pytest hooks shared by the whole test suite."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Fail fast with a clear message when runtime deps are missing.

    Many tests import ``garage_os.storage`` (via CLI, knowledge, etc.), which
    requires ``filelock`` and ``PyYAML``. A bare ``pip install pytest`` leaves
    those absent, producing dozens of obscure collection errors.
    """
    checks: list[tuple[str, str, str]] = [
        ("filelock", "filelock", "filelock"),
        ("yaml", "PyYAML", "pyyaml"),
    ]
    missing: list[str] = []
    for import_name, label, _pip in checks:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(label)
    if missing:
        joined = "\n  - ".join(missing)
        raise pytest.UsageError(
            "Missing runtime dependencies for Garage OS tests:\n"
            f"  - {joined}\n\n"
            "Install project dependencies, for example:\n"
            "  pip install -e .\n"
            "  uv sync\n"
            "  poetry install\n"
            "(see pyproject.toml → [tool.poetry.dependencies])"
        )
