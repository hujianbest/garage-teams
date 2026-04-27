# TypeScript Style Template (F016 — well-known defaults)

Each `- prefix: content` line below becomes a `KnowledgeType.STYLE` entry on
`garage memory ingest --style-template typescript`.

- `strict-mode-required`: `"strict": true` in tsconfig.json; reject implicit `any`, unused locals, unchecked array access.
- `prefer-readonly-arrays`: Use `readonly T[]` or `ReadonlyArray<T>` for parameters that should not be mutated.
- `no-default-export`: Prefer named exports over default exports for refactor-friendliness and consistent imports.
- `interface-over-type-alias`: Use `interface` for object shapes; reserve `type` for unions, intersections, mapped types.
- `discriminated-unions`: Model state with discriminated unions (`{ kind: "loading" } | { kind: "ready"; data: T }`) instead of optional fields.
- `prefer-const-assertions`: Use `as const` for literal type narrowing instead of explicit type annotations.
- `no-non-null-assertion`: Avoid `!` non-null assertion; use proper narrowing or runtime check.
- `async-await-over-then`: Use `async/await` over `.then()` chains for readability; only mix when error handling requires it.
