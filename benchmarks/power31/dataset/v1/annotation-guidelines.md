# POWER 3.1 Synthetic Benchmark — Annotation Guidelines

## Scope
This is a SYNTHETIC benchmark generated deterministically by code.
All relevance judgements are topic-driven, not human-annotated.

## Relevance Scale
- 2 (High): Primary document — directly answers the query
- 1 (Medium): Secondary related document
- 0 (None): No relevant information

## Utility Scale
- +0.8: Primary document, directly resolves the query
- +0.3: Secondary, partially relevant
- 0.0: No utility (implicit — no qrels entry)
- -0.5: Distractor (topically similar but contradictory)

## Sparse Qrels
Only positive and distractor entries are stored.
Missing (query_id, document_id) pairs imply relevance=0.

## No-Answer Queries
No-answer queries have no qrels entries (all implicit zero).

## Distractor Queries
QDD* queries have a primary document AND a topically similar
contradictory distractor document with negative utility.

## Limitation
This is NOT human annotation. Do not cite this as production evidence.
