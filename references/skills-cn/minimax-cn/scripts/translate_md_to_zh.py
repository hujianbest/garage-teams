#!/usr/bin/env python3
"""
Translate Markdown files to zh-CN while preserving fenced code blocks.
Uses deep-translator (Google); chunk to respect length limits.
"""
from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    raise SystemExit("pip install deep-translator")

CHUNK = 4500
SLEEP = 0.35


def split_fenced(text: str) -> list[tuple[str, str]]:
    """Return list of ('text'|'code', segment)."""
    out: list[tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        j = text.find("```", i)
        if j == -1:
            if i < n:
                out.append(("text", text[i:]))
            break
        if j > i:
            out.append(("text", text[i:j]))
        k = text.find("```", j + 3)
        if k == -1:
            out.append(("text", text[j:]))
            break
        out.append(("code", text[j : k + 3]))
        i = k + 3
    return out


def mostly_chinese(s: str) -> bool:
    if not s.strip():
        return True
    cjk = sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")
    letters = sum(1 for ch in s if ch.isalpha() and ord(ch) < 128)
    return cjk > letters * 0.4


def translate_chunks(translator: GoogleTranslator, s: str) -> str:
    if not s.strip() or mostly_chinese(s):
        return s
    parts: list[str] = []
    pos = 0
    n = len(s)
    while pos < n:
        end = min(pos + CHUNK, n)
        chunk = s[pos:end]
        if end < n:
            cut = chunk.rfind("\n", CHUNK // 2)
            if cut != -1:
                chunk = chunk[: cut + 1]
        if chunk.strip():
            for attempt in range(3):
                try:
                    parts.append(translator.translate(chunk))
                    time.sleep(SLEEP)
                    break
                except Exception:
                    if attempt == 2:
                        parts.append(chunk)
                    else:
                        time.sleep(2.0 * (attempt + 1))
        pos += len(chunk)
    return "".join(parts)


def translate_file(path: Path, translator: GoogleTranslator, dry_run: bool) -> str | None:
    raw = path.read_text(encoding="utf-8")
    segments = split_fenced(raw)
    new_parts: list[str] = []
    for kind, seg in segments:
        if kind == "code":
            new_parts.append(seg)
            continue
        if dry_run:
            new_parts.append(seg)
            continue
        new_parts.append(translate_chunks(translator, seg) if seg.strip() else seg)
    return "".join(new_parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="Root directory to scan for .md")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", help="Relative paths under root only")
    ap.add_argument(
        "--skip-name",
        nargs="*",
        default=(
            "README.md",
            "README_en.md",
            "README_zh.md",
            "INTRODUCTION_zh.md",
        ),
        help="Basenames to skip (default: locale/readme variants)",
    )
    ap.add_argument("--max-files", type=int, default=0, help="0 = no limit")
    args = ap.parse_args()
    root: Path = args.root.resolve()
    translator = GoogleTranslator(source="auto", target="zh-CN")
    md_files = sorted(root.rglob("*.md"))
    skip = set(args.skip_name)
    md_files = [p for p in md_files if p.name not in skip]
    if args.only:
        only = {root / p.replace("\\", "/") for p in args.only}
        md_files = [p for p in md_files if p in only or str(p.relative_to(root)) in args.only]
    if args.max_files:
        md_files = md_files[: args.max_files]
    for i, path in enumerate(md_files):
        rel = path.relative_to(root)
        print(f"[{i+1}/{len(md_files)}] {rel}")
        try:
            out = translate_file(path, translator, args.dry_run)
            if out is not None and not args.dry_run:
                path.write_text(out, encoding="utf-8", newline="\n")
        except Exception as e:
            print(f"  FAIL: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
