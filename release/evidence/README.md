# Release evidence

Run the POWER 3.1 harness to create a local JSON evidence artifact:

```bash
PYTHONPATH=src python3 benchmarks/power31/scripts/evaluation/run_release_evaluation.py \
  --timestamp 2026-07-22T00:00:00+00:00 \
  --output release/evidence/power31-evidence.json
PYTHONPATH=src python3 benchmarks/power31/scripts/evaluation/verify_evidence.py \
  release/evidence/power31-evidence.json
```

JSON artifacts are intentionally ignored because each run records the exact
working-tree commit, hardware and model state and should be archived by CI or
the release process, not committed as mutable repository state.
