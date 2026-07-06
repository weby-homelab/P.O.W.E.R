# MCP Server

The P.O.W.E.R. Framework exposes its full functionality via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), enabling AI agents to interact with your Obsidian vault directly.

## Running

```bash
python -m power_framework.mcp
```

Or via a direct script:

```python
from power_framework.mcp.power_server import run
import asyncio

asyncio.run(run())
```

## Available Tools

### `lint_vault`

Run health checks on a vault. Returns metadata issues, broken links, and orphans.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vault_path` | `string` | No | Path to vault root |

### `generate_index`

Compile hierarchical index (`index.md` + per-folder `_index.md` files).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vault_path` | `string` | No | Path to vault root |

### `read_sub_index`

Read a specific P.A.R.A. category sub-index on-demand.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | `string` | Yes | Folder name (e.g. `01_Projects`) |
| `vault_path` | `string` | No | Path to vault root |

### `ingest_note`

Create a new note with strict OKF metadata frontmatter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | Note filename |
| `note_type` | `string` | Yes | Type (`Project`, `Area`, etc.) |
| `title` | `string` | Yes | Page title |
| `description` | `string` | Yes | Short description |
| `content` | `string` | Yes | Body content |
| `resource` | `string` | No | External URL |
| `tags` | `string[]` | No | List of tags |
| `vault_path` | `string` | No | Path to vault root |

### `search_vault_tool`

Full-text search across vault notes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `string` | Yes | Search query |
| `max_results` | `integer` | No | Max results (default: 20) |
| `vault_path` | `string` | No | Path to vault root |

### `synthesize_session` *(new in v1.6.0)*

Create a session synthesis note with auto-classified OKF frontmatter, governance metadata, Graph RAG links, and full index/log maintenance. Implements the Agent Auto-Ingest Feedback Loop.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | Filename (e.g. `2026-07-06_session.md`) |
| `title` | `string` | Yes | Session title |
| `description` | `string` | Yes | Short summary |
| `content` | `string` | Yes | Body content |
| `note_type` | `string` | No | Default: `Daily Log` |
| `tags` | `string[]` | No | List of tags |
| `related` | `string[]` | No | Graph RAG links to related notes |
| `owner` | `string` | No | Responsible entity |
| `vault_path` | `string` | No | Path to vault root |

### `run_rot_audit` *(new in v1.7.0)*

Run a ROT (Redundant, Outdated, Trivial) audit on the vault. Returns categorized issues.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vault_path` | `string` | No | Path to vault root |

### `archive_stale_notes` *(new in v1.7.0)*

Auto-archive stale notes older than the threshold to `04_Archive/`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stale_days` | `integer` | No | Days without change to consider stale (default: 90) |
| `dry_run` | `boolean` | No | Preview without moving (default: true) |
| `vault_path` | `string` | No | Path to vault root |

### `suggest_related_notes` *(new in v1.7.0)*

Suggest cross-note relations based on keyword and tag overlap analysis.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_path` | `string` | No | Analyze relations for a specific note |
| `max_results` | `integer` | No | Maximum suggestions (default: 10) |
| `vault_path` | `string` | No | Path to vault root |

### `heal_frontmatter_tool` *(new in v1.7.1)*

Scan and heal missing/invalid frontmatter fields across vault notes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dry_run` | `boolean` | No | Preview without editing (default: true) |
| `vault_path` | `string` | No | Path to vault root |

### `check_markdown_tool` *(new in v1.7.1)*

Check markdown quality issues across the vault: trailing whitespace, list markers, header jumps, code language.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vault_path` | `string` | No | Path to vault root |
