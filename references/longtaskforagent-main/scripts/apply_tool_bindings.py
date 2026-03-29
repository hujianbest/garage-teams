#!/usr/bin/env python3
"""
Render SKILL.md.template files using Jinja2 with tool-bindings.json context.

Templates use Jinja2 syntax:
- {{ cap_ui_navigate }} etc. for UI tool name substitution
- {{ cap_ci_coverage }} etc. for CI capability tool names
- {% if enterprise_mcp %} for enterprise-only sections
- {% if has_mcp_ci %} for CI MCP sections (hidden when no enterprise CI config)
- {% if has_mcp_ui %} for enterprise UI tool sections

Rendered .md files are written to the project-local output directory
(default: .long-task-bindings/), NOT to the plugin directory.  This avoids
concurrent-session race conditions when multiple projects are open.

Use --regenerate-defaults to update the committed SKILL.md files in the
plugin's skills/ directory (developer workflow after editing templates).

Usage:
    python scripts/apply_tool_bindings.py tool-bindings.json
    python scripts/apply_tool_bindings.py tool-bindings.json --output-dir .long-task-bindings
    python scripts/apply_tool_bindings.py tool-bindings.json --dry-run
    python scripts/apply_tool_bindings.py --defaults
    python scripts/apply_tool_bindings.py --regenerate-defaults
    python scripts/apply_tool_bindings.py --quiet

Exit codes:
    0 — all templates rendered successfully
    1 — one or more errors (unless --quiet)
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    print(
        "ERROR: jinja2 is required. Install with: pip install jinja2",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Default context (Chrome DevTools MCP tool names)
# ---------------------------------------------------------------------------

DEFAULT_CONTEXT: dict[str, object] = {
    # Flags
    "enterprise_mcp": False,
    "has_mcp_ui": False,
    "has_mcp_ci": False,

    # UI tools (Chrome DevTools MCP defaults — always provided)
    "cap_ui_platform":    "Chrome DevTools MCP",
    "cap_ui_navigate":    "navigate_page",
    "cap_ui_wait":        "wait_for",
    "cap_ui_snapshot":    "take_snapshot",
    "cap_ui_screenshot":  "take_screenshot",
    "cap_ui_click":       "click",
    "cap_ui_fill":        "fill",
    "cap_ui_key":         "press_key",
    "cap_ui_eval":        "evaluate_script",
    "cap_ui_console":     "list_console_messages",
    "cap_ui_hover":       "hover",
    "cap_ui_drag":        "drag",
    "cap_ui_network":     "list_network_requests",

    # CI tools (empty — not used without enterprise config)
    "cap_ci_test":       "",
    "cap_ci_coverage":   "",
    "cap_ci_mutation":   "",
}

# Mapping: tool-bindings.json ui_tools.tool_mapping canonical names → context var
_CANONICAL_TO_VAR: dict[str, str] = {
    "navigate_page":         "cap_ui_navigate",
    "wait_for":              "cap_ui_wait",
    "take_snapshot":         "cap_ui_snapshot",
    "take_screenshot":       "cap_ui_screenshot",
    "click":                 "cap_ui_click",
    "fill":                  "cap_ui_fill",
    "press_key":             "cap_ui_key",
    "evaluate_script":       "cap_ui_eval",
    "list_console_messages": "cap_ui_console",
    "hover":                 "cap_ui_hover",
    "drag":                  "cap_ui_drag",
    "list_network_requests": "cap_ui_network",
}


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------

def build_context(bindings: dict | None) -> dict[str, object]:
    """
    Build Jinja2 template context from tool-bindings.json or defaults.

    Args:
        bindings: Parsed tool-bindings.json dict, or None for defaults.

    Returns:
        Dict of template variables.
    """
    ctx: dict[str, object] = dict(DEFAULT_CONTEXT)

    if bindings is None:
        return ctx

    caps = bindings.get("capability_bindings", {})

    # UI tool mapping
    ui_mapping = caps.get("ui_tools", {}).get("tool_mapping", {})
    if ui_mapping:
        ctx["has_mcp_ui"] = True
        ctx["enterprise_mcp"] = True
        for canonical_name, value in ui_mapping.items():
            var_name = _CANONICAL_TO_VAR.get(canonical_name)
            if var_name:
                ctx[var_name] = value

    # CI capabilities
    for cap_key, var_name in [("test", "cap_ci_test"),
                               ("coverage", "cap_ci_coverage"),
                               ("mutation", "cap_ci_mutation")]:
        cap = caps.get(cap_key, {})
        if cap.get("type") == "mcp" and cap.get("tool"):
            ctx["has_mcp_ci"] = True
            ctx["enterprise_mcp"] = True
            ctx[var_name] = cap["tool"]

    # Platform name: derive from first MCP server name
    if ui_mapping:
        mcp_servers = bindings.get("mcp_servers", {})
        if mcp_servers:
            first_server = next(iter(mcp_servers))
            ctx["cap_ui_platform"] = f"{first_server} MCP"

    return ctx


# ---------------------------------------------------------------------------
# Jinja2 rendering
# ---------------------------------------------------------------------------

def render_template(template_path: Path, context: dict[str, object]) -> str:
    """
    Render a single Jinja2 template file.

    Args:
        template_path: Path to .md.template file.
        context: Template variables from build_context().

    Returns:
        Rendered Markdown content.
    """
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    tmpl = env.get_template(template_path.name)
    return tmpl.render(**context)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_plugin_root() -> Path:
    """Locate the plugin root directory (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def find_templates(plugin_root: Path) -> list[tuple[Path, Path]]:
    """
    Find all .md.template files and their output paths (relative to skills/).

    Returns:
        List of (template_path, relative_output_path) tuples.
        relative_output_path is relative to the output directory.
    """
    templates = []
    skills_dir = plugin_root / "skills"

    for tmpl in skills_dir.rglob("*.md.template"):
        rel = tmpl.relative_to(plugin_root / "skills")
        output_rel = rel.with_suffix("")  # removes .template → .md
        templates.append((tmpl, Path("skills") / output_rel))

    return templates


# ---------------------------------------------------------------------------
# Main render loop
# ---------------------------------------------------------------------------

def render_all(
    plugin_root: Path,
    output_dir: Path,
    bindings: dict | None,
    dry_run: bool = False,
    quiet: bool = False,
) -> int:
    """
    Render all templates and write to output_dir.

    Returns:
        Number of errors encountered.
    """
    templates = find_templates(plugin_root)
    if not templates:
        msg = f"No .md.template files found under {plugin_root / 'skills'}"
        print(msg, file=sys.stderr)
        return 1

    context = build_context(bindings)
    errors = 0
    rendered = 0

    for tmpl_path, rel_output in templates:
        out_path = output_dir / rel_output

        try:
            rendered_content = render_template(tmpl_path, context)
        except Exception as e:  # noqa: BLE001
            print(f"[apply_tool_bindings] ERROR rendering {tmpl_path}: {e}",
                  file=sys.stderr)
            errors += 1
            continue

        if dry_run:
            print(f"[dry-run] Would write: {out_path}")
            rendered += 1
            continue

        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            rendered += 1
        except OSError as e:
            print(f"[apply_tool_bindings] ERROR writing {out_path}: {e}",
                  file=sys.stderr)
            errors += 1

    if not quiet or errors:
        label = "dry-run" if dry_run else "rendered"
        print(
            f"[apply_tool_bindings] {rendered} templates {label}"
            + (f", {errors} errors" if errors else ""),
            file=sys.stderr if quiet else sys.stdout,
        )

    return errors


def regenerate_defaults(plugin_root: Path, dry_run: bool = False) -> int:
    """
    Render all templates with default context and write back to plugin
    skills/ directory (updating the committed SKILL.md files).

    Returns:
        Number of errors encountered.
    """
    templates = find_templates(plugin_root)
    if not templates:
        msg = f"No .md.template files found under {plugin_root / 'skills'}"
        print(msg, file=sys.stderr)
        return 1

    context = build_context(None)  # default context
    errors = 0
    rendered = 0

    for tmpl_path, rel_output in templates:
        # Write to plugin directory (not output_dir)
        out_path = plugin_root / rel_output

        try:
            rendered_content = render_template(tmpl_path, context)
        except Exception as e:  # noqa: BLE001
            print(f"[regenerate] ERROR rendering {tmpl_path}: {e}",
                  file=sys.stderr)
            errors += 1
            continue

        if dry_run:
            print(f"[dry-run] Would write: {out_path}")
            rendered += 1
            continue

        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            rendered += 1
        except OSError as e:
            print(f"[regenerate] ERROR writing {out_path}: {e}",
                  file=sys.stderr)
            errors += 1

    label = "dry-run" if dry_run else "regenerated"
    print(f"[apply_tool_bindings] {rendered} defaults {label}"
          + (f", {errors} errors" if errors else ""))

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render SKILL.md.template files with Jinja2 tool bindings"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "bindings", nargs="?", default=None,
        help="Path to tool-bindings.json (enterprise MCP mode)"
    )
    group.add_argument(
        "--defaults", action="store_true",
        help="Render with default Chrome DevTools MCP values (no tool-bindings.json needed)"
    )
    group.add_argument(
        "--regenerate-defaults", action="store_true",
        help="Regenerate committed SKILL.md files from templates using defaults"
    )
    parser.add_argument(
        "--output-dir", default=".long-task-bindings",
        help="Output directory for rendered files (default: .long-task-bindings)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be written without writing files"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Only output warnings/errors to stderr; suppress normal output"
    )
    args = parser.parse_args()

    plugin_root = find_plugin_root()

    # Regenerate defaults mode
    if args.regenerate_defaults:
        errors = regenerate_defaults(plugin_root, dry_run=args.dry_run)
        sys.exit(1 if errors else 0)

    output_dir = Path(args.output_dir).resolve()

    # Resolve bindings
    bindings: dict | None = None
    if args.defaults:
        bindings = None
    elif args.bindings:
        try:
            with open(args.bindings, "r", encoding="utf-8") as f:
                bindings = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: {args.bindings} not found", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: Cannot parse {args.bindings}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        bindings = None

    errors = render_all(
        plugin_root=plugin_root,
        output_dir=output_dir,
        bindings=bindings,
        dry_run=args.dry_run,
        quiet=args.quiet,
    )

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
