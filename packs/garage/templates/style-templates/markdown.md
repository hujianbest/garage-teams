# Markdown Style Template (F016 — well-known defaults)

Each `- prefix: content` line below becomes a `KnowledgeType.STYLE` entry on
`garage memory ingest --style-template markdown`.

- `atx-headers-only`: Use ATX-style headers (`# Title`) only; no setext underline-style headers.
- `code-fence-language-tag`: Always tag code fences with a language (` ```python`); use `text` for plain text.
- `relative-links-for-repo`: Repo-internal references use relative paths; external use full URL.
- `front-matter-yaml`: Front matter uses YAML (`---`); not TOML, not JSON.
- `bullet-style-hyphen`: Use `-` for bullet lists (not `*` or `+`); keep one consistent marker per file.
- `numbered-lists-1-1`: Numbered lists use `1.` `1.` `1.` (markdown auto-numbers); easier to reorder.
- `no-line-break-at-end-of-line`: Don't add trailing whitespace for hard line breaks; use blank line for paragraphs.
