# dataset/v1 Changelog

## v2 — 2026-07-22

- Complete methodological redesign (E1 review)
- Topic-driven: 50 frozen topics with bilingual UA/EN content
- Exactly 200 answerable queries (50/stratum), no random primary assignment
- 228 queries (208 answerable, 20 no-answer)
- 100 corpus documents, 416 sparse qrels entries
- Atomic answers are literal substrings of primary documents
- Generator: `generate_benchmark.py` (seed=42)
- Scope: synthetic only — not human annotation
