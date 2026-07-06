# CLI Reference

## Synopsis

```
power [-h] [-v] {init,lint,index,ingest,search,rot,archive,cron,suggest-related} ...
```

## Global options

| Flag | Description |
|------|-------------|
| `-h`, `--help` | Show help message |
| `-v`, `--version` | Show version |

## Commands

### `init`

Scaffold a new OKF-compliant vault.

```
power init path
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to create the vault directory |

### `lint`

Run health checks on a vault.

```
power lint path
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |

Checks:
- Missing or invalid YAML frontmatter
- Broken internal links (`[[wikilinks]]`)
- Orphan notes (not linked from any other note)
- Metadata completeness (type, title, description)

### `index`

Generate hierarchical indexes.

```
power index path
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |

Creates `index.md` (overview) and per-folder `_index.md` (detailed entries).

### `ingest`

Create a new note with validated OKF metadata.

```
power ingest path --type TYPE --title TITLE --description DESC [--tags TAGS] [--resource URL] [--overwrite]
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |
| `--type`, `-t` | Yes | Note type (`Project`, `Area`, `Resource`, `Daily Log`, `Archive`, `System Guide`) |
| `--title` | Yes | Note title |
| `--description` | Yes | One-line description (max 150 chars) |
| `--tags` | No | Space-separated tags |
| `--resource` | No | URL to external resource |
| `--overwrite` | No | Overwrite existing note |

### `search`

Full-text search across vault notes.

```
power search path query [--max-results MAX_RESULTS]
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |
| `query` | Yes | Search query (supports multiple terms and "quoted phrases") |
| `--max-results`| No | Maximum number of results (default: 20) |

### `rot`

ROT Audit — detect redundant, outdated, and trivial notes.

```
power rot path [--stale-days STALE_DAYS] [--min-body-chars MIN_BODY_CHARS]
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |
| `--stale-days` | No | Days without change to consider stale (default: 90) |
| `--min-body-chars` | No | Minimum body characters (default: 50) |

### `archive`

Auto-archive stale notes to `04_Archive/`.

```
power archive path [--stale-days STALE_DAYS] [--dry-run]
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |
| `--stale-days` | No | Days without change to consider stale (default: 90) |
| `--dry-run` | No | Preview which notes would be archived without moving them |

### `suggest-related`

Suggest cross-note relations for Graph RAG enrichment.

```
power suggest-related path [--target TARGET_PATH] [--max-results MAX_RESULTS]
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |
| `--target` | No | Analyze relations for a specific note path |
| `--max-results` | No | Maximum number of suggestions (default: 5) |

### `cron`

Run automated maintenance: lint + index + rot audit.

```
power cron path
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `path` | Yes | Path to the vault directory |
