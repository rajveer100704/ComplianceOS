---
name: documentation
description: >
  Use when maintaining and updating documentation across the repository: README,
  API docs, ARCHITECTURE, ADRs, ROADMAP, CHANGELOG, deployment guides, and runtime runbooks.
---

# Documentation Skill

## When to Use

- Completing a feature implementation or bug fix.
- Updating API contracts or configuration settings.
- Adding architectural diagrams or screenshot assets.
- Updating release notes or CHANGELOG entries.

## Documentation Update Matrix

| Change Type | Required Documentation Updates |
| :--- | :--- |
| **New API Endpoint** | `README.md` (endpoint list), `docs/README.md`, OpenAPI schema |
| **Schema Change** | `database/migrations/`, `ARCHITECTURE.md` (if model scope changes) |
| **New Auth Provider** | `docs/security/SECURITY_ENGINEERING.md`, `README.md`, `config/settings.py` |
| **Architectural Choice** | New ADR in `docs/adr/`, `ARCHITECTURE.md` |
| **Bug Fix / Patch** | `CHANGELOG.md` |
| **Release / Tag** | `ROADMAP.md`, `CHANGELOG.md`, Release Notes |

## Documentation Standards

1. **Clear Links**: Use GitHub-style markdown file links with relative paths (`[Deployment Guide](docs/deployment-guide.md)`).
2. **Syntax Highlighting**: Always specify language identifiers on code blocks (````python`, ````bash`, ````json`).
3. **No Stale Examples**: Ensure all code snippets in documentation compile and match active API signatures.
4. **Visual Assets**: Embed screenshots and diagrams directly into documentation using relative image paths (`docs/images/`).

## Checklist

- [ ] `README.md` reflects current features and quickstart steps.
- [ ] `docs/README.md` index includes all updated or new documents.
- [ ] `CHANGELOG.md` updated under the `[Unreleased]` or version section.
- [ ] Relative links verified to work.
- [ ] No hardcoded tokens, passwords, or personal credentials in docs.

## References

- [AGENTS.md](../../AGENTS.md)
- [docs/README.md](../../docs/README.md)
