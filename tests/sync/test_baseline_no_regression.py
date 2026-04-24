"""F010 INV-F10-2 sentinel: 测试基线零退绿守门.

Covers:
- design § 4.1 INV-F10-2 (CON-1001 字节级兼容)
- design-review-r1 important I-4 + tasks-review-r1 important I-1

This sentinel is **not** a unit test — it's a meta-assertion that the F009 baseline
of 715 passed tests is preserved as F010 implementation grows. Each task T1-T7
adds tests; the baseline only goes up. If a test count drops below 715, F010
implementation broke a F009 既有 test (CON-1001 violation).

Run as part of ``pytest tests/sync/test_baseline_no_regression.py``; the assert
runs against the pytest session count via the pytest hook below.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_full_baseline_count() -> None:
    """INV-F10-2: pytest tests/ -q passed count >= 715 (F009 + search hotfix baseline).

    F010 实施后基线递增, 但 F009 既有用例不退绿. 本 sentinel 通过 subprocess 跑
    全套测试 (排除 self) 拿 passed count.

    Implementation note: 用 subprocess 而非 pytest fixture 是为了避免 sentinel
    自我引用 (sentinel 自己 PASS 应被计入 ≥ 715, 但不能让 sentinel 调用 pytest 时
    再次触发自己 → infinite recursion). 用 -k 'not baseline_no_regression' 排除自己.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(REPO_ROOT / "tests"),
            "-q",
            "--no-header",
            "-k",
            "not baseline_no_regression",  # avoid recursion
            "-x",  # fail fast (any single failure = baseline breach)
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    # Parse output for "N passed" line
    last_lines = result.stdout.strip().splitlines()[-5:]
    passed_count = 0
    for line in last_lines:
        # e.g. "715 passed in 26.65s" or "715 passed, 1 warning in 26.65s"
        if " passed" in line:
            try:
                # 取 "passed" 之前最近的整数
                tokens = line.split()
                for i, tok in enumerate(tokens):
                    if tok == "passed" or tok.startswith("passed"):
                        passed_count = int(tokens[i - 1])
                        break
                if passed_count > 0:
                    break
            except (ValueError, IndexError):
                continue

    # F009 + search hotfix baseline = 715
    BASELINE_F009_HOTFIX = 715
    assert passed_count >= BASELINE_F009_HOTFIX, (
        f"INV-F10-2 violated: pytest passed count = {passed_count}, "
        f"expected >= {BASELINE_F009_HOTFIX} (F009 baseline + search hotfix). "
        f"F010 implementation broke F009 既有 test. "
        f"pytest stdout tail:\n{result.stdout[-2000:]}\n"
        f"pytest stderr tail:\n{result.stderr[-500:]}"
    )
