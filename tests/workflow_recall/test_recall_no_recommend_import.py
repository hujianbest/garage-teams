"""F014 T5 sentinel: CON-1405 — recall is independent of F006 recommend.

`garage recall workflow` is a sibling of `garage recommend`; the recall
implementation MUST NOT import / depend on the recommend code path
(recommend pushes content; recall pushes workflow paths — strict
separation per CON-1405).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _module_imports(file_path: Path) -> set[str]:
    """Return the set of `from X import` and `import X` module names parsed
    statically (no runtime import side-effects)."""
    src = file_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(file_path))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module)
    return out


def test_recall_module_does_not_import_recommend() -> None:
    """All workflow_recall/*.py files MUST NOT import recommend-specific modules."""
    pkg_dir = REPO_ROOT / "src" / "garage_os" / "workflow_recall"
    forbidden_substrings = ("recommend", "recommendation_service")

    for py_file in pkg_dir.glob("*.py"):
        imports = _module_imports(py_file)
        for imp in imports:
            for bad in forbidden_substrings:
                assert bad not in imp, (
                    f"CON-1405 violated: {py_file.relative_to(REPO_ROOT)} "
                    f"imports '{imp}' which contains forbidden token '{bad}'. "
                    "Workflow recall is a sibling of F006 recommend; the "
                    "implementations must remain strictly independent."
                )
