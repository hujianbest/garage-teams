#!/usr/bin/env python3
"""
Check retrospective feedback authorization status.

Checks:
- REST API endpoint is configured (feature-list.json retro_api_endpoint or RETRO_API_ENDPOINT env var)
- Endpoint is reachable (HTTP HEAD with 5s timeout)

Usage:
    python check_retro_auth.py <path/to/feature-list.json>

Exit codes:
    0 — ready (endpoint configured and reachable)
    1 — unavailable (endpoint configured but not reachable)
    2 — disabled (no endpoint configured)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def check_retro_auth(path: str) -> dict:
    """
    Check retrospective feedback authorization status.

    Args:
        path: Path to feature-list.json

    Returns:
        dict with keys:
            status: "ready" | "unavailable" | "disabled"
            endpoint: str or None
            error: str or None
    """
    result = {
        "status": "disabled",
        "endpoint": None,
        "error": None,
    }

    # Load feature-list.json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Check retro_api_endpoint field in feature-list.json
    endpoint = data.get("retro_api_endpoint")

    # 2. Fall back to env var if not in JSON
    if not endpoint:
        endpoint = os.environ.get("RETRO_API_ENDPOINT")

    # 3. If neither → disabled
    if not endpoint:
        return result

    result["endpoint"] = endpoint

    # 4. Try HTTP HEAD request with 5s timeout
    try:
        req = urllib.request.Request(endpoint, method="HEAD")
        response = urllib.request.urlopen(req, timeout=5)
        # 5. Any 2xx/3xx → ready (urlopen raises on 4xx/5xx by default)
        result["status"] = "ready"
    except Exception as e:
        # 6. Timeout, connection error, 4xx/5xx → unavailable
        result["status"] = "unavailable"
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="Check retrospective feedback authorization status")
    parser.add_argument("path", help="Path to feature-list.json")
    args = parser.parse_args()

    try:
        result = check_retro_auth(args.path)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: Cannot read feature-list.json: {e}")
        sys.exit(1)

    status = result["status"]
    endpoint = result["endpoint"]
    error = result["error"]

    if status == "ready":
        print(f"Retrospective feedback: ready ({endpoint})")
        sys.exit(0)
    elif status == "unavailable":
        print(f"Retrospective feedback: unavailable ({endpoint} — {error})")
        sys.exit(1)
    else:
        print("Retrospective feedback: disabled (no endpoint configured)")
        sys.exit(2)


if __name__ == "__main__":
    main()
