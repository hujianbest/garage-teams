# Security Policy

`garage-agent` is a local-first agent capability home. The threat model is small but not zero: the runtime touches files outside the repository (host directories like `~/.claude/`, `~/.cursor/`, `~/.config/opencode/`), shells out to `git` for `pack install / publish`, and ingests host conversation history that may contain secrets.

If you find a security issue, thank you for taking the time to report it.

## Supported versions

While the project is pre-1.0, only the latest tagged release on `main` receives security fixes.

| Version | Supported |
|---|---|
| `main` (HEAD) | ✅ |
| `v0.1.x` | ✅ |
| Anything older | ❌ |

## Reporting a vulnerability

**Please do not open a public GitHub issue for vulnerabilities.**

Preferred channel:

1. Open a private security advisory on GitHub:
   <https://github.com/hujianbest/garage-agent/security/advisories/new>
2. Or email the maintainer (see GitHub profile of [@hujianbest](https://github.com/hujianbest))

Please include:

- A description of the issue and its impact
- Steps to reproduce (or a minimal proof-of-concept)
- Affected version / commit SHA
- Whether the issue is already public anywhere
- Any suggested mitigation

We will:

- Acknowledge receipt within 5 business days
- Provide an initial assessment (severity + planned fix window) within 10 business days
- Coordinate a fix and disclosure timeline with you (typically 30–90 days depending on severity)
- Credit you in the release notes unless you prefer to remain anonymous

## What counts as a vulnerability

In scope:

- Path traversal or unintended file writes during `garage init`, `pack install / update / uninstall / publish`, `sync`, `session import`, or `knowledge export`
- Secret leakage through `pack publish` (the sensitive-pattern scan is meant to block this; bypass = security bug)
- Secret leakage through `knowledge export --anonymize` (the 7-rule anonymizer is meant to redact; bypass = security bug)
- Code injection via crafted `pack.json`, `SKILL.md` front matter, or imported host conversation history
- Privilege escalation across project / user scope (`--scope project|user`)
- Manifest or schema-migration issues that silently corrupt user data in `.garage/`

Out of scope (please file as a normal issue or discussion):

- Issues that require the user to run `garage pack publish ... --force` (explicit opt-out of safety scan)
- Issues that require pre-existing local file-system compromise
- Bugs in third-party hosts (Claude Code, Cursor, OpenCode) unless garage-agent's adapter triggers them
- Denial of service from very large `.garage/` directories on resource-constrained machines

## Coordinated disclosure

Once a fix is ready, we will:

1. Cut a patch release
2. Publish a GitHub Security Advisory with the CVE (if assigned), affected versions, fix version, and credit
3. Note the fix in `RELEASE_NOTES.md`

Thank you for helping keep `garage-agent` and its users safe.
