# POWER 3.1.0 release evidence

POWER 3.1.0 is a release candidate specification. Runtime behavior and
documentation must be backed by reproducible, versioned artifacts before
production claims are made.

## What is pinned

The canonical dense model is the `bge-m3-onnx` export listed in
[`release/models.lock.json`](https://github.com/weby-homelab/power-framework/blob/main/release/models.lock.json),
including upstream/export revisions, licenses, file hashes, and sizes. The
optional Jina cross-encoder is non-commercial (`CC-BY-NC-4.0`) and requires
explicit opt-in; it is not a production default.

## Benchmark status

`benchmarks/power31` is a deterministic synthetic bilingual corpus. It is
useful for hermetic CI regression gates only: it is not human annotated, does
not contain real vault notes, and cannot establish production retrieval
quality, latency, or memory claims. Historical 3.0 reports are retained for
context and are diagnostic only. UDCG in those reports is a legacy lexical
proxy, not the EACL-2026 metric.

## Release gates

The [trust-release ADR](adr/0001-power-3.1-trust-release-baseline.md) defines
the fail-closed retrieval, MCP boundary/transport, provenance, and evidence
requirements. A release evaluation must retain its manifest, dependency lock,
hardware profile, model revisions, raw outputs, and verifier result. Until the
P0/P1 gates are closed, POWER remains beta/research software.

Run the benchmark integrity checks locally with:

```bash
python -m pytest benchmarks/power31/tests/ -v --no-cov --override-ini="addopts="
```
