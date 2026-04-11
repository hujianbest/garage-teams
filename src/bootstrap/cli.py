"""Minimal Garage CLI entry that reuses the shared SessionApi seam."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .install_layout import package_version, resolve_runtime_home, resolve_source_root, resolve_workspace_root
from .launcher import BootstrapConfig, BootstrapError, LaunchMode
from .runtime_home_doctor import DoctorSeverity, diagnose_runtime_home, findings_as_jsonable
from .runtime_ops import compute_install_diagnostics
from .session_api import SessionApi


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="garage",
        description="Garage CLIEntry built on the shared bootstrap and SessionApi chain.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a new Garage session.")
    _add_common_arguments(create)
    create.add_argument("--problem-kind", required=True, help="Problem kind for the new session.")
    create.add_argument("--entry-pack", required=True, help="Entry pack id.")
    create.add_argument("--entry-node", required=True, help="Entry node id.")
    create.add_argument("--goal", required=True, help="Primary goal for the session.")
    create.add_argument("--summary", help="Optional session summary override.")
    create.add_argument(
        "--boundary",
        action="append",
        default=[],
        help="Boundary statement to include in the session intent. Repeatable.",
    )

    resume = subparsers.add_parser("resume", help="Resume an existing Garage session.")
    _add_common_arguments(resume)
    resume.add_argument("--session-id", required=True, help="Session id to resume.")

    attach = subparsers.add_parser("attach", help="Attach to an existing active Garage session.")
    _add_common_arguments(attach)
    attach.add_argument("--session-id", required=True, help="Session id to attach.")

    doctor = subparsers.add_parser("doctor", help="Validate runtime home layout, profile, and credentials.")
    doctor.add_argument(
        "--runtime-home",
        type=Path,
        default=None,
        help="Runtime home root; defaults to GARAGE_RUNTIME_HOME or the OS user-local layout.",
    )
    doctor.add_argument("--profile-id", default="default", help="Runtime profile id to validate.")
    doctor.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (for example missing directories) as failures.",
    )

    status = subparsers.add_parser("status", help="Print local runtime diagnostics (no session required).")
    _add_common_arguments(status)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    if argv_list and argv_list[0] in ("--version", "-V"):
        sys.stdout.write(f"garage {package_version()}\n")
        return 0

    parser = build_parser()
    args = parser.parse_args(argv_list)
    try:
        if args.command == "doctor":
            runtime_home = resolve_runtime_home(args.runtime_home)
            findings, ok = diagnose_runtime_home(runtime_home, profile_id=args.profile_id)
            if args.strict:
                ok = ok and not any(f.severity == DoctorSeverity.WARNING for f in findings)
            payload = {
                "ok": ok,
                "findings": findings_as_jsonable(findings),
            }
            json.dump(payload, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0 if ok else 1

        if args.command == "status":
            payload = compute_install_diagnostics(
                source_root=resolve_source_root(args.source_root),
                runtime_home=resolve_runtime_home(args.runtime_home),
                workspace_root=resolve_workspace_root(args.workspace_root),
                workspace_id=args.workspace_id,
                profile_id=args.profile_id,
                entry_surface="cli",
                host_adapter_id=args.host_adapter_id,
            )
            json.dump(payload, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0

        api = SessionApi()
        config = _config_from_args(args)
        if args.command == "create":
            result = api.create(config)
        elif args.command == "resume":
            result = api.resume(config)
        else:
            result = api.attach(config)
        payload = api.summarize(result).as_mapping()
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (BootstrapError, ValueError) as exc:
        print(f"garage: {exc}", file=sys.stderr)
        return 1


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Garage source root; defaults to cwd or GARAGE_SOURCE_ROOT when set.",
    )
    parser.add_argument(
        "--runtime-home",
        type=Path,
        default=None,
        help="Runtime home root; defaults to GARAGE_RUNTIME_HOME or the OS user-local layout.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root; defaults to the current working directory.",
    )
    parser.add_argument("--workspace-id", help="Explicit workspace id. Defaults to the workspace folder name.")
    parser.add_argument("--profile-id", default="default", help="Runtime profile id to use.")
    parser.add_argument("--host-adapter-id", help="Explicit host adapter binding to use.")
    parser.add_argument("--initiator", default="creator", help="Initiator id recorded in the session intent.")


def _config_from_args(args: argparse.Namespace) -> BootstrapConfig:
    common_kwargs = {
        "source_root": resolve_source_root(args.source_root),
        "runtime_home": resolve_runtime_home(args.runtime_home),
        "workspace_root": resolve_workspace_root(args.workspace_root),
        "workspace_id": args.workspace_id,
        "profile_id": args.profile_id,
        "entry_surface": "cli",
        "host_adapter_id": args.host_adapter_id,
        "initiator": args.initiator,
    }
    if args.command == "create":
        return BootstrapConfig(
            launch_mode=LaunchMode.CREATE,
            problem_kind=args.problem_kind,
            entry_pack=args.entry_pack,
            entry_node=args.entry_node,
            goal=args.goal,
            summary=args.summary,
            boundaries=tuple(args.boundary),
            **common_kwargs,
        )
    if args.command == "resume":
        return BootstrapConfig(
            launch_mode=LaunchMode.RESUME,
            session_id=args.session_id,
            **common_kwargs,
        )
    return BootstrapConfig(
        launch_mode=LaunchMode.ATTACH,
        session_id=args.session_id,
        **common_kwargs,
    )


if __name__ == "__main__":
    raise SystemExit(main())
