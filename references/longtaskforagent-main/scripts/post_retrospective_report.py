#!/usr/bin/env python3
"""
Post retrospective records to configured REST API endpoint.

Compresses docs/retrospectives/*.md into a tar.gz and POSTs it
as multipart/form-data to the configured endpoint.

Configuration sources (priority order):
1. feature-list.json root field "retro_api_endpoint"
2. Environment variable RETRO_API_ENDPOINT

Usage:
    python post_retrospective_report.py --feature-list feature-list.json
    python post_retrospective_report.py --feature-list feature-list.json --retro-dir docs/retrospectives
    python post_retrospective_report.py --feature-list feature-list.json --api-key $RETRO_API_KEY

Exit codes:
    0 — success
    1 — failure (no endpoint, no records, HTTP error)
"""

import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request


def _make_multipart(fields: dict, files: dict) -> tuple:
    """
    Build a multipart/form-data body.

    Args:
        fields: dict of field_name -> string_value
        files: dict of field_name -> (filename, file_bytes, content_type)

    Returns:
        (content_type, body_bytes)
    """
    boundary = "----RetrospectiveBoundary9876543210"
    parts = []

    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        parts.append(f"{value}\r\n".encode())

    for name, (filename, data, content_type) in files.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; '
            f'filename="{filename}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        parts.append(data)
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())

    body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, body


def post_retrospective(
    feature_list_path: str,
    retro_dir: str = "docs/retrospectives",
    api_key: str | None = None,
) -> dict:
    """
    Post retrospective records to configured REST API endpoint.

    Args:
        feature_list_path: Path to feature-list.json.
        retro_dir: Path to retrospectives directory.
        api_key: Optional API key for Authorization header.

    Returns:
        dict with keys:
            success: bool
            message: str
            endpoint: str or None
            record_count: int
    """
    result = {
        "success": False,
        "message": "",
        "endpoint": None,
        "record_count": 0,
    }

    # 1. Read feature-list.json
    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        result["message"] = f"Cannot read feature-list.json: {e}"
        return result

    # 2. Resolve endpoint
    endpoint = data.get("retro_api_endpoint")
    if not endpoint:
        endpoint = os.environ.get("RETRO_API_ENDPOINT")
    if not endpoint:
        result["message"] = "No endpoint configured"
        return result
    result["endpoint"] = endpoint

    # 3. Glob .md files (top-level only, exclude subdirectories)
    md_files = sorted(glob.glob(os.path.join(retro_dir, "*.md")))
    if not md_files:
        result["message"] = "No records to report"
        return result
    result["record_count"] = len(md_files)

    # 4. Create tar.gz in temp directory
    try:
        tmpdir = tempfile.mkdtemp()
        tar_path = os.path.join(tmpdir, "retrospectives.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            for md_path in md_files:
                tar.add(md_path, arcname=os.path.basename(md_path))

        # 5. Get project name
        project_name = data.get("project", "unknown")

        # 6. Get branch
        try:
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            branch = "unknown"

        # 7. Get current date
        date_str = datetime.date.today().isoformat()

        # 8. Build multipart request
        with open(tar_path, "rb") as f:
            tar_bytes = f.read()

        fields = {
            "project": project_name,
            "date": date_str,
            "branch": branch,
            "record_count": str(len(md_files)),
        }
        files = {
            "file": ("retrospectives.tar.gz", tar_bytes, "application/gzip"),
        }

        content_type, body = _make_multipart(fields, files)

        # 9. POST
        headers = {"Content-Type": content_type}

        # 10. Resolve API key
        resolved_key = api_key or os.environ.get("RETRO_API_KEY")
        if resolved_key:
            headers["Authorization"] = f"Bearer {resolved_key}"

        req = urllib.request.Request(
            endpoint, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                resp.read()
                result["success"] = True
                result["message"] = (
                    f"Posted {len(md_files)} records to {endpoint}"
                )
        except urllib.error.HTTPError as e:
            result["message"] = f"HTTP {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            result["message"] = f"URL error: {e.reason}"

    finally:
        # Cleanup temp files
        if os.path.exists(tar_path):
            os.unlink(tar_path)
        if os.path.isdir(tmpdir):
            os.rmdir(tmpdir)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Post retrospective records to REST API"
    )
    parser.add_argument(
        "--feature-list",
        required=True,
        help="Path to feature-list.json",
    )
    parser.add_argument(
        "--retro-dir",
        default="docs/retrospectives",
        help="Path to retrospectives directory (default: docs/retrospectives)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for Authorization header",
    )
    args = parser.parse_args()

    result = post_retrospective(
        args.feature_list, args.retro_dir, args.api_key
    )

    if result["success"]:
        print(result["message"])
        sys.exit(0)
    else:
        print(f"ERROR: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
