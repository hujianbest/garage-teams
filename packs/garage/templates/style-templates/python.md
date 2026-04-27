# Python Style Template (F016 — well-known defaults)

Each `- prefix: content` line below becomes a `KnowledgeType.STYLE` entry on
`garage memory ingest --style-template python`. Edit / delete entries as
needed — they're starting points, not commandments.

- `prefer-functional-python`: Prefer functional patterns (map / filter / list comprehensions) over class-based when state is not required.
- `type-hints-required`: All public functions must have type hints; rely on Python 3.11+ syntax (`X | None` over `Optional[X]`).
- `f-string-over-percent`: Prefer f-strings over `%` or `.format()` for string interpolation.
- `pathlib-over-os-path`: Use `pathlib.Path` instead of `os.path` for filesystem operations; keep paths as `Path`, not `str`.
- `dataclass-over-tuple`: Prefer `@dataclass` over `NamedTuple` or raw tuples for new structured types.
- `pytest-fixture-naming`: Pytest fixtures use lowercase names; test functions follow `test_<intent>_<expected>` pattern.
- `no-mutable-default-args`: Never use mutable default arguments; use `None` + sentinel pattern (`x = x if x is not None else []`).
