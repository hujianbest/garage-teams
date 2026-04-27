"""F015 T4 sentinel: CON-1505 — agent_compose 不 import 其他 sibling subcommand.

The agent_compose package MUST be independent of:
- F006 recommend (`recommendation_service`)
- F013-A skill_mining
- F014 workflow_recall

Each is a sibling subcommand under `garage`; their implementations should not
become entangled. AST-level static analysis catches this without runtime imports.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _module_imports(file_path: Path) -> set[str]:
    """Return the set of imported module names parsed statically."""
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


def test_agent_compose_does_not_import_siblings() -> None:
    """All agent_compose/*.py files MUST NOT import other sibling subcommand modules."""
    pkg_dir = REPO_ROOT / "src" / "garage_os" / "agent_compose"
    forbidden_substrings = (
        "recommendation_service",
        "skill_mining",
        "workflow_recall",
    )

    for py_file in pkg_dir.glob("*.py"):
        imports = _module_imports(py_file)
        for imp in imports:
            for bad in forbidden_substrings:
                assert bad not in imp, (
                    f"CON-1505 violated: {py_file.relative_to(REPO_ROOT)} "
                    f"imports '{imp}' which contains forbidden token '{bad}'. "
                    "Agent compose is a sibling subcommand of F006/F013-A/F014; "
                    "implementations must remain strictly independent."
                )
