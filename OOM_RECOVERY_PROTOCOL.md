# OOM Recovery & Low-RAM Deployment Protocol (v2.2.1)

This protocol documents the OOM incident on `power sync` / background
indexing and the safeguards added in **v2.2.0** + **v2.2.1** so POWER runs
safely on 8–12 GB hosts (e.g. an i5-5200U / 16 GB DDR3 node) and does not
blow up on many-core hosts.

---

## 1. What happened (root cause)

### 1a. Per-item embedding (v2.2.0, fixed)

`power sync` (and the background `index_worker`) called
`_sync_vault_to_db(..., sync_embeddings=True)`, which embedded **every
document and every chunk with a per-item `embed()` call** — no `batch_size`,
no thread limit. On the default model
(`paraphrase-multilingual-MiniLM-L12-v2`, 12 layers, ~470 MB + torch
runtime) this pinned **9.4 GB RSS in a single thread** and saturated all 4
CPU cores, tripping the kernel OOM-killer and spiking ZFS write interrupts
(`z_wr_int` at ~41% CPU).

### 1b. `parallel=0` spawned one model per CPU core (v2.2.1, fixed)

`FastEmbedManager.embed_batch` passed `parallel=0` to fastembed. fastembed
interprets `parallel=0` as **"one subprocess per CPU core"**, and **each
subprocess loads its own copy of the model + ONNXRuntime arena**.

- On a **20-core WS** with a heavy model (`BAAI/bge-m3`, ~2.3 GB) this
  spawned **20 model processes** → **~32 GB RSS** (the incident reported).
- On PRXMX-01 (4 cores, bge-m3) it spawned 4 processes → ~8 GB RSS, already
  eating more than half of the 15 GB box.

This was masked in v2.2.0 because the per-item path held peak RAM down, but
the parallel fan-out dominated on many-core hosts. **Fixed in v2.2.1**:
`parallel` is now bounded to `POWER_EMBED_NUM_THREADS` (default `2`), so peak
RSS is `threads × model_size` (≈ 700 MB for MiniLM, ≈ 5 GB for bge-m3) **regardless
of core count**.

---

## 2. Fixes shipped

| Area                                | Change                                                                                                                                                                                | Env var                                   |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Batched embedding                   | `_sync_vault_to_db` now collects changed files, then embeds **doc + chunk vectors in batches** via `embed_batch`. Peak RAM is bounded by `batch_size`, not vault size.                | `POWER_EMBED_BATCH_SIZE` (default `8`)    |
| Adaptive shrink                     | On any allocation failure (incl. ONNXRuntime arena `Fail`), `batch_size` halves and retries down to 1; at `bs=1` the item is **skipped** (logged) instead of aborting the whole sync. | —                                         |
| Thread capping                      | Embedding engine bounded to `OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS`.                                                                                                               | `POWER_EMBED_NUM_THREADS` (default `2`)   |
| Streamed commits                    | Vectors are committed to SQLite every `POWER_EMBED_COMMIT_EVERY` items, so the WAL never buffers the whole vault (fixes the ZFS write spike).                                         | `POWER_EMBED_COMMIT_EVERY` (default `50`) |
| **Parallel fan-out bound (v2.2.1)** | `embed_batch` no longer passes `parallel=0` (one model subprocess per core). It is bounded to `POWER_EMBED_NUM_THREADS`, so peak RSS = `threads × model_size` on **any** core count.  | `POWER_EMBED_NUM_THREADS` (default `2`)   |
| Process vmem cap (opt-in)           | `power sync` can apply an `RLIMIT_AS` backstop. **Disabled by default** (0) because some backends legitimately need >6 GB for their inference arena.                                  | `POWER_SYNC_VMEM_LIMIT_MB` (default `0`)  |

---

## 3. Recommended low-RAM deployment (8–12 GB)

Add to the environment / systemd unit / supervisor:

```bash
# --- 8 GB hosts: use the small multilingual MiniLM (default, ~470 MB) ---
# (this is the POWER default; set explicitly for clarity)
export POWER_EMBED_PROVIDER=fastembed
# Keep the box responsive on low-core CPUs
export POWER_EMBED_NUM_THREADS=2
# Bound peak embedding RAM; halves automatically on pressure
export POWER_EMBED_BATCH_SIZE=16

# --- 12 GB+ hosts: better cross-lingual quality with Qwen3-0.6B ONNX ---
# export POWER_EMBED_PROVIDER=qwen3
# NOTE: Qwen3-0.6B allocates a ~2.3 GB ONNXRuntime arena per matmul node on
# CPU, so it needs >=12 GB. The sync now skips (not crashes) if even bs=1
# cannot be allocated.

# Hard backstop (opt-in): kill the sync before the kernel OOM-killer does (MB).
# Leave at 0 unless you are SURE the model fits; 0 disables the cap.
export POWER_SYNC_VMEM_LIMIT_MB=0

# Persistent model-weight cache (downloaded once, reused across runs)
export XDG_CACHE_HOME=/var/cache/power-framework
```

### Model / RAM matrix (measured)

| Provider (model)                                               | Weights    | Peak RSS @ batch (CPU) | Min RAM   | Use case                                                           |
| -------------------------------------------------------------- | ---------- | ---------------------- | --------- | ------------------------------------------------------------------ |
| `fastembed` (`paraphrase-multilingual-MiniLM-L12-v2`, default) | ~470 MB    | ~700 MB @ threads=2    | **8 GB**  | Default; multilingual; safe on small nodes                         |
| `fastembed` (`BAAI/bge-m3`)                                    | ~2.3 GB    | ~5 GB @ threads=2      | **12 GB** | Higher quality; set via `POWER_EMBEDDING_MODEL` — **needs ≥12 GB** |
| `qwen3` (`Qwen3-Embedding-0.6B-ONNX`)                          | ~1.2 GB    | ~6–8 GB (2.3 GB arena) | **12 GB** | Best UA↔EN quality; opt-in                                         |
| `ollama` (`qwen3-embedding:0.6b`)                              | via Ollama | depends on Ollama      | 12 GB+    | When Ollama already present                                        |

### Centralized embedding server (optional, for 8 GB)

For very tight hosts, run a single shared `remote-embedding` server and
point POWER at it so the model is loaded **once** instead of per-process:

```bash
pip install remote-embedding
remote-embedding-server \
  --model-name BAAI/bge-small-en-v1.5 \
  --device cpu \
  --max-loaded-models 1 \
  --max-inputs-per-request 128 \
  --embedding-batch-size 32 \
  --clear-cuda-cache-after-request
```

Then set `POWER_EMBED_PROVIDER=remote` (or keep `fastembed` local — the
server is mainly useful when multiple tools share one embedding model).

---

## 4. Recovery steps if a sync is killed

1. The SQLite index uses WAL + `incremental_vacuum`, so a killed sync leaves
   a consistent (possibly partially-stale) DB. Just re-run:
    ```bash
    power sync /path/to/vault --fts-only   # cheap, re-builds FTS only
    power sync /path/to/vault              # re-embeddings with batching
    ```
2. If the `.power_search.db` is corrupted (rare), delete it and rebuild:
    ```bash
    rm -f ~/.cache/power-framework/power_search.db*
    power sync /path/to/vault
    ```
3. Verify peak RSS stayed bounded:
    ```bash
    /usr/bin/time -v power sync /path/to/vault 2>&1 | grep "Maximum resident"
    ```
    Expected: **< 3.5 GB** on the ONNX backend with `batch_size=32`.

---

## 5. Regression guard

`tests/test_low_ram_sync.py` asserts that sync uses `embed_batch` (never
per-item `embed`), survives a simulated `MemoryError`, and skips embedding
entirely in FTS-only mode. Run it with:

```bash
pytest tests/test_low_ram_sync.py -v
```
