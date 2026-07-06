# Architecture

## Package layout

```
src/power_framework/
├── __init__.py         # Public API exports
├── core/
│   ├── __init__.py     # Re-exports all core modules
│   ├── cli.py          # CLI entry point (argparse) — 9 commands
│   ├── models.py       # OKFMetadata, NoteType, constants
│   ├── parser.py       # YAML frontmatter parsing
│   ├── linter.py       # Vault health checks (links, metadata, orphans, stale notes, ROT audit)
│   ├── indexer.py      # Hierarchical index generation
│   ├── relations.py    # Entity extraction + relation suggestions (Graph RAG)
│   ├── searcher.py     # Full-text search with scoring
│   └── utils.py        # Path safety, atomic writes, version
└── mcp/
    ├── __init__.py
    ├── __main__.py     # python -m entry point
    └── power_server.py # FastMCP server (9 tools)

tests/
├── test_cli.py         # CLI functional tests
├── test_indexer.py     # Indexer unit tests
├── test_integration.py # Full-cycle integration tests
├── test_linter.py      # Linter tests
├── test_mcp_server.py  # MCP tool tests
├── test_models.py      # Model validation tests
├── test_parser.py      # Parser tests
├── test_relations.py   # Relation suggestions tests
├── test_rot.py         # ROT audit tests
├── test_searcher.py    # Search scoring tests
└── test_security.py    # Path traversal + atomic write tests
```

## Design decisions

- **`src/` layout** — Standard Python packaging practice, prevents import confusion
- **FastMCP** — Decorator-based MCP server, ~60% less boilerplate than raw Server
- **Pydantic v2** — `model_dump()` instead of `dict()`, strict validation
- **Atomic file writes** — `os.replace()` for crash-safe config persistence
- **Pure Python** — Zero external runtime deps beyond `mcp`, `pydantic`, `pyyaml`
