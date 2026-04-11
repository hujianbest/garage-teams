#!/usr/bin/env python3
"""Minimal release smoke checks and compatibility snapshot (T191).

Run from the repository root:

    python scripts/release_smoke.py

Blockers: failing unittest suite, CLI version, or doctor on a synthetic runtime home.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Curated support snapshot — adjust as adapters and platforms are validated.
COMPATIBILITY_MATRIX: dict[str, object] = {
    "cli_entry": {"status": "supported", "notes": "garage CLI via pip install -e . or wheel"},
    "runtime_home_doctor": {"status": "supported", "notes": "garage doctor"},
    "host_bridge_entry": {"status": "experimental", "notes": "API seam present; host-specific adapters T210-T212"},
    "web_entry": {"status": "experimental", "notes": "local control plane skeleton"},
    "os": {
        "linux": "supported",
        "darwin": "expected_ok_unverified",
        "win32": "supported",
    },
    "python": {"min": "3.12", "tested": "3.12+"},
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _env_with_src(repo: Path) -> dict[str, str]:
    merged = dict(os.environ)
    src = str(repo / "src")
    prev = merged.get("PYTHONPATH", "")
    merged["PYTHONPATH"] = src if not prev else f"{src}{os.pathsep}{prev}"
    return merged


def _run_unit_tests(repo: Path, env: dict[str, str]) -> None:
    print("== smoke: unittest discover")
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=repo,
        env=env,
        check=True,
    )


def _run_cli_version(repo: Path, env: dict[str, str]) -> None:
    print("== smoke: garage --version")
    subprocess.run(
        [sys.executable, "-m", "bootstrap.cli", "--version"],
        cwd=repo,
        env=env,
        check=True,
    )


def _run_doctor_on_synthetic_home(repo: Path, env: dict[str, str]) -> None:
    print("== smoke: doctor on synthetic runtime home")
    with tempfile.TemporaryDirectory() as tmp:
        rh = Path(tmp) / "runtime-home"
        for sub in ("profiles", "config", "adapters", "cache"):
            (rh / sub).mkdir(parents=True)
        (rh / "profiles" / "smoke.json").write_text(
            json.dumps(
                {
                    "providerId": "provider.smoke",
                    "modelId": "model.smoke",
                    "adapterId": "adapter.smoke",
                }
            ),
            encoding="utf-8",
        )
        (rh / "adapters" / "adapter.smoke.json").write_text(
            json.dumps({"providerId": "provider.smoke"}),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "bootstrap.cli",
                "doctor",
                "--runtime-home",
                str(rh),
                "--profile-id",
                "smoke",
            ],
            cwd=repo,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stdout)
            print(proc.stderr, file=sys.stderr)
            raise SystemExit(f"doctor smoke failed with exit {proc.returncode}")


def _run_status_smoke(repo: Path, env: dict[str, str], runtime_home: Path, workspace_root: Path) -> None:
    print("== smoke: status / diagnostics")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "bootstrap.cli",
            "status",
            "--source-root",
            str(repo),
            "--runtime-home",
            str(runtime_home),
            "--workspace-root",
            str(workspace_root),
            "--profile-id",
            "smoke",
        ],
        cwd=repo,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout, file=sys.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"status smoke failed with exit {proc.returncode}")
    import json as _json

    payload = _json.loads(proc.stdout)
    if payload.get("health") != "healthy":
        raise SystemExit(f"status smoke: expected healthy diagnostics, got {payload.get('health')!r}")


def main() -> int:
    repo = _repo_root()
    env = _env_with_src(repo)
    print("Garage compatibility matrix (informational):")
    print(json.dumps(COMPATIBILITY_MATRIX, indent=2, sort_keys=True))
    print()
    try:
        _run_unit_tests(repo, env)
        _run_cli_version(repo, env)
        with tempfile.TemporaryDirectory() as tmp:
            rh = Path(tmp) / "runtime-home"
            ws = Path(tmp) / "workspace"
            ws.mkdir()
            for sub in ("profiles", "config", "adapters", "cache"):
                (rh / sub).mkdir(parents=True)
            (rh / "profiles" / "smoke.json").write_text(
                json.dumps(
                    {
                        "providerId": "provider.smoke",
                        "modelId": "model.smoke",
                        "adapterId": "adapter.smoke",
                    }
                ),
                encoding="utf-8",
            )
            (rh / "adapters" / "adapter.smoke.json").write_text(
                json.dumps({"providerId": "provider.smoke"}),
                encoding="utf-8",
            )
            _run_status_smoke(repo, env, rh, ws)
        _run_doctor_on_synthetic_home(repo, env)
    except subprocess.CalledProcessError as exc:
        print(f"release_smoke: subprocess failed: {exc}", file=sys.stderr)
        return 1
    print("release_smoke: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
