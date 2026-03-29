#!/usr/bin/env python3
"""
SessionStart / SessionEnd Hook: Session Cleanup  (long-task-agent plugin, plugin-level)

On SessionStart: Takes a snapshot of all currently listening TCP ports and PIDs.
On SessionEnd:   Compares snapshot to current state; kills only the processes
                 that started DURING the session (differential cleanup).

Registered in hooks/hooks.json for both SessionStart and SessionEnd events.
Fires automatically for every session where the long-task-agent plugin is installed.

The script distinguishes between the two events by the presence/absence of
the snapshot file: if no snapshot exists → SessionStart; if snapshot exists →
SessionEnd.

--- SNAPSHOT FORMAT ---
Stored at: /tmp/claude-st-snapshot-<session_id>.json
Content:   {"port": pid, ...}  — mapping of port → PID at session start.

--- GRACEFUL DEGRADATION ---
Works for any project. When no services are running at session start, the
snapshot is empty and cleanup is a no-op.

--- DEPENDENCIES ---
Optional: psutil (pip install psutil) — falls back to stdlib if unavailable.
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import tempfile


# ---------------------------------------------------------------------------
# Runtime port → pid discovery
# ---------------------------------------------------------------------------

def _get_listening() -> dict[int, int]:
    """Return {port: pid} for all currently listening TCP sockets."""
    try:
        import psutil  # type: ignore

        result: dict[int, int] = {}
        for conn in psutil.net_connections(kind="tcp"):
            if getattr(conn, "status", None) == "LISTEN" and conn.pid and conn.laddr:
                p = conn.laddr.port
                if 1024 <= p <= 65535:
                    result[p] = conn.pid
        return result
    except ImportError:
        return _stdlib_listening()


def _stdlib_listening() -> dict[int, int]:
    result: dict[int, int] = {}
    try:
        if platform.system() == "Windows":
            out = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=8
            ).stdout
            for line in out.splitlines():
                if "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        addr, pid_str = parts[1], parts[-1]
                        port_str = addr.rsplit(":", 1)[-1]
                        try:
                            p, pid = int(port_str), int(pid_str)
                            if 1024 <= p <= 65535:
                                result[p] = pid
                        except ValueError:
                            pass
        else:
            try:
                out = subprocess.run(
                    ["ss", "-tlnp"], capture_output=True, text=True, timeout=5
                ).stdout
                for line in out.splitlines():
                    m = re.search(r":(\d+)\s.*pid=(\d+)", line)
                    if m:
                        p, pid = int(m.group(1)), int(m.group(2))
                        if 1024 <= p <= 65535:
                            result[p] = pid
            except FileNotFoundError:
                out = subprocess.run(
                    ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
                    capture_output=True, text=True, timeout=8
                ).stdout
                for line in out.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 9:
                        port_str = parts[8].rsplit(":", 1)[-1]
                        pid_str = parts[1]
                        try:
                            p, pid = int(port_str), int(pid_str)
                            if 1024 <= p <= 65535:
                                result[p] = pid
                        except ValueError:
                            pass
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return result


# ---------------------------------------------------------------------------
# Process termination
# ---------------------------------------------------------------------------

def _kill_pid(pid: int) -> bool:
    try:
        import psutil  # type: ignore

        psutil.Process(pid).kill()
        return True
    except Exception:
        pass
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True, timeout=5
            )
        else:
            os.kill(pid, 9)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _snapshot_path(session_id: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"claude-st-snapshot-{session_id}.json")


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
        session_id: str = data.get("session_id", "default")
    except (json.JSONDecodeError, AttributeError, TypeError):
        session_id = "default"

    snap_path = _snapshot_path(session_id)

    if not os.path.isfile(snap_path):
        # ── SessionStart: take snapshot ──────────────────────────────────
        listening = _get_listening()
        try:
            with open(snap_path, "w", encoding="utf-8") as f:
                json.dump({str(p): pid for p, pid in listening.items()}, f)
            print(
                f"[session-cleanup] Snapshot saved ({len(listening)} listening ports)",
                file=sys.stderr,
            )
        except OSError as e:
            print(f"[session-cleanup] WARNING: cannot write snapshot: {e}", file=sys.stderr)
    else:
        # ── SessionEnd: differential cleanup ────────────────────────────
        try:
            with open(snap_path, encoding="utf-8") as f:
                old_snapshot: dict[str, int] = json.load(f)
        except (json.JSONDecodeError, OSError):
            old_snapshot = {}

        old_pids = set(old_snapshot.values())
        current = _get_listening()

        cleaned: list[str] = []
        for port, pid in current.items():
            if pid not in old_pids:
                if _kill_pid(pid):
                    cleaned.append(f"port {port} (PID {pid})")

        if cleaned:
            print(
                f"[session-cleanup] Cleaned session processes: {', '.join(cleaned)}",
                file=sys.stderr,
            )
        else:
            print("[session-cleanup] No session processes to clean.", file=sys.stderr)

        # Remove snapshot file
        try:
            os.remove(snap_path)
        except OSError:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
