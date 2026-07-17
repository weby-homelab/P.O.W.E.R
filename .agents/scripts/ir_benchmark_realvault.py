"""Real-vault IR benchmark on /root/gemma/brain (no gold labels).

Measures latency for all 5 modes and dumps top-1/top-5 per query for
qualitative analysis. No MRR/nDCG (no gold relevance), complementing
the synthetic-corpus benchmark which has gold labels.
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from power_framework.core.searcher import search_vault

VAULT = Path("/root/gemma/brain")
MODES = ["fts", "vector", "hybrid"]

QUERIES = [
    "docker deployment container",
    "GPG signing git commit",
    "LLM inference speed benchmark GPU",
    "Proxmox LXC container network configuration",
    "FastAPI security authentication endpoint",
    "Pydantic validation schema metadata",
    "knowledge base second brain obsidian notes",
    "GitHub Actions CI CD workflow release",
    "VPN Tailscale network tunnel",
    "firewall security hardening audit",
    "MCP server agent tool integration",
    "backup archive storage Samba",
    "Power Safety Ukraine power outage",
    "embedding vector semantic search RAG",
    "docker container security deployment settings",
    "резервне копіювання бази даних postgres",
    "GPG signing git commit authentication",
    "налаштування VPN Tailscale мережевий тунель",
    "резервне копіювання бази даних",
    "firewall hardening security audit rules",
    "швидкість інференсу LLM на GPU бенчмарк",
    "MCP server agent tool integration protocol",
    "контейнер Proxmox LXC мережева конфігурація",
    "Obsidian second brain knowledge base notes",
    "автентифікація FastAPI безпека endpoint",
    "backup archive storage Samba share",
    "настройка фаервола аудит безопасности",
    "SSH port change configuration hardening",
    "синхронізація ролей бази знань автоматична",
    "semantic vector embedding search RAG",
    "відмова від галюцинацій пошук неіснуючих фактів",
    "оновлення зв'язків перейменування нотаток",
    "граф знань зв'язки проект база даних",
]


def main() -> None:
    print("Warming up on real vault:", VAULT)
    t0 = time.time()
    search_vault(VAULT, "warmup docker container", mode="hybrid_reranked", max_results=5)
    print(f"Warmup took {time.time() - t0:.2f}s")

    lat: dict[str, list[float]] = {m: [] for m in MODES}
    top1: dict[str, list[str | None]] = {m: [] for m in MODES}
    top5: dict[str, list[list[str]]] = {m: [] for m in MODES}

    for q in QUERIES:
        for m in MODES:
            t0 = time.time()
            res = search_vault(VAULT, q, mode=m, max_results=20)
            dt = time.time() - t0
            lat[m].append(dt)
            top1[m].append(res[0].rel_path if res else None)
            top5[m].append([r.rel_path for r in res[:5]])

    summary = {}
    for m in MODES:
        l = lat[m]
        summary[m] = {
            "AvgLatency": round(statistics.mean(l), 3),
            "MinLatency": round(min(l), 3),
            "P95Latency": round(sorted(l)[int(0.95 * (len(l) - 1))], 3),
            "MaxLatency": round(max(l), 3),
        }

    out = {
        "vault": str(VAULT),
        "n_files": 559,
        "summary": summary,
        "top1": top1,
        "queries": QUERIES,
    }
    Path("/tmp/power_eval_realvault.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"n_files": 559, "summary": summary}, ensure_ascii=False, indent=2))
    # Print a few top-1 examples for qualitative check
    print("\n=== Sample Top-1 (first 6 queries) ===")
    for i in range(6):
        print(f"Q: {QUERIES[i]}")
        for m in MODES:
            print(f"   {m:16s} -> {top1[m][i]}")


if __name__ == "__main__":
    main()
