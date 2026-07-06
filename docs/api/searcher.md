# Searcher

Full-text search with relevance scoring using SQLite FTS5 (with memory fallback).

| Function | Returns | Description |
|----------|---------|-------------|
| `search_vault(vault_dir, query, max_results, mode)` | `list[SearchResult]` | Search the vault with configurable mode: `fts` (BM25, default), `vector` (TF cosine), `hybrid` (RRF fusion) |
| `format_search_results(results, query, mode)` | `str` | Format search results into a human-readable report string |

## `SearchResult`

Class representing a single search result with relevance details.

| Attribute | Type | Description |
|-----------|------|-------------|
| `rel_path` | `str` | Note relative path |
| `title` | `str` | Note title |
| `description` | `str` | Note description |
| `note_type` | `str` | Note OKF type |
| `score` | `float` | Weighted relevance score |
| `snippet` | `str` | Context window around match |
| `match_count` | `int` | Match count fallback |
| `tags` | `list[str]` | List of tags associated with the note |

