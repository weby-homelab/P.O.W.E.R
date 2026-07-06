# ROT Scoring

Track A2 scoring: content deduplication, freshness monitoring, link rot detection, and usage tracking (all without external embeddings).

| Class / Function | Description |
|------------------|-------------|
| `ContentDedupDetector` | TF-Vector cosine similarity for body content |
| `FreshnessScorer` | Type-based exponential decay freshness scoring |
| `LinkRotChecker` | HTTP HEAD checks for external URL health |
| `UsageTracker` | SQLite-based access counter (thread-safe) |

## `ContentDedupDetector`

```python
detector = ContentDedupDetector(threshold=0.75)
pairs: list[tuple[str, str, float]] = detector.detect(vault_dir)
```

- Uses `_compute_tf_vector` and `_cosine_similarity` from `searcher.py` (no external embeddings)
- Threshold defaults to `0.75` — pairs below threshold are not reported
- Skips notes with fewer than 20 body tokens
- Returns sorted list of `(path_a, path_b, similarity_score)`

## `FreshnessScorer`

```python
scorer = FreshnessScorer()
scores: dict[str, float] = scorer.score_all(vault_dir)
```

- Scores each note `0.0` (stale) to `1.0` (fresh)
- Uses exponential decay: `score = 2^(-age_days / half_life_days)`
- Half-life depends on note type:

| Type | Half-life |
|------|-----------|
| Daily Log | 30 days |
| Project | 180 days |
| Area | 365 days |
| Resource | 365 days |
| System Guide | 365 days |
| Archive | 730 days |

## `LinkRotChecker`

```python
checker = LinkRotChecker(timeout=5)
broken: dict[str, list[tuple[str, int]]] = checker.check_all(vault_dir)
```

- Performs HTTP HEAD requests on external markdown links
- Returns dict mapping `rel_path` → `[(url, status_code)]` for broken links only (status >= 400 or connection error)
- Connection error returns status `-1`

## `UsageTracker`

```python
tracker = UsageTracker(vault_dir)
tracker.track_access("01_Projects/note.md")
count = tracker.get_count("01_Projects/note.md")
all_counts: dict[str, int] = tracker.get_all_counts()
```

- Thread-safe SQLite storage (`.power_usage.db` in vault root)
- `track_access()` upserts with increment
- `get_all_counts()` returns dict of `rel_path → access_count`
