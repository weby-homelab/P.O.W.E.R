"""Regression tests for POWER 3.1 frozen benchmark dataset integrity (E1).

Tests are hermetic — no network, no model, no private vault.
They verify the committed benchmark dataset is internally consistent,
including content support (atomic answers are substrings of primary docs).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

BENCHMARK_ROOT = Path(__file__).resolve().parent.parent
DATASET_V1 = BENCHMARK_ROOT / "dataset" / "v1"

REQUIRED_FILES = [
    "queries.jsonl",
    "qrels.synthetic.jsonl",
    "expected-answers.jsonl",
    "corpus-manifest.json",
    "annotation-guidelines.md",
]

ABSENT_TOKENS = {"TensorFlow", "S3", "React", "RabbitMQ", "Elasticsearch"}
STRATA = {"ua_to_ua", "en_to_en", "ua_to_en", "en_to_ua"}
BASE_ANSWERABLE_PER_STRATUM = 50
N_ABSENT = 5
N_DISTRACTOR = 8


# ── Fixtures (plain functions — no classmethod deprecation warnings) ──────


def _load_jsonl(name: str) -> list[dict]:
    path = DATASET_V1 / name
    items: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


@pytest.fixture(scope="module")
def queries() -> list[dict]:
    return _load_jsonl("queries.jsonl")


@pytest.fixture(scope="module")
def qrels() -> list[dict]:
    return _load_jsonl("qrels.synthetic.jsonl")


@pytest.fixture(scope="module")
def answers() -> list[dict]:
    return _load_jsonl("expected-answers.jsonl")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((DATASET_V1 / "corpus-manifest.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus() -> dict[str, str]:
    return {f.name: f.read_text(encoding="utf-8") for f in (DATASET_V1 / "corpus").glob("*.md")}


@pytest.fixture(scope="module")
def doc_ids(manifest: dict) -> set[str]:
    return {e["document_id"] for e in manifest["corpus"]["files"]}


@pytest.fixture(scope="module")
def query_ids(queries: list[dict]) -> set[str]:
    return {q["query_id"] for q in queries}


# ── Required files ────────────────────────────────────────────────────────


class TestRequiredFiles:
    def test_all_required_files_exist(self) -> None:
        for name in REQUIRED_FILES:
            assert (DATASET_V1 / name).exists(), f"missing: {name}"

    def test_corpus_dir_exists(self) -> None:
        assert (DATASET_V1 / "corpus").is_dir()

    def test_no_adjudicated_qrels(self) -> None:
        assert not (DATASET_V1 / "qrels.adjudicated.jsonl").exists()


# ── Query counts and structure ────────────────────────────────────────────


class TestQueryCounts:
    def test_total_queries(self, queries: list[dict]) -> None:
        assert len(queries) == 228, f"total queries: {len(queries)}"

    def test_exact_50_base_per_stratum(self, queries: list[dict]) -> None:
        for s in STRATA:
            base = sum(
                1
                for q in queries
                if q["stratum"] == s
                and q["query_class"] != "no_answer"
                and not q["query_id"].startswith("QDD")
            )
            assert base == BASE_ANSWERABLE_PER_STRATUM, f"stratum {s}: {base} base answerable"

    def test_exactly_8_qdd(self, queries: list[dict]) -> None:
        qdd = [q for q in queries if q["query_id"].startswith("QDD")]
        assert len(qdd) == N_DISTRACTOR

    def test_exactly_20_no_answer(self, queries: list[dict]) -> None:
        na = [q for q in queries if q["query_class"] == "no_answer"]
        assert len(na) == N_ABSENT * 4

    def test_5_no_answer_per_stratum(self, queries: list[dict]) -> None:
        for s in STRATA:
            na = sum(1 for q in queries if q["stratum"] == s and q["query_class"] == "no_answer")
            assert na == N_ABSENT, f"stratum {s}: {na} no-answer"

    def test_no_no_answer_in_qdd(self, queries: list[dict]) -> None:
        for q in queries:
            if q["query_id"].startswith("QDD"):
                assert q["query_class"] != "no_answer"

    def test_unique_ids(self, queries: list[dict]) -> None:
        ids = [q["query_id"] for q in queries]
        assert len(set(ids)) == len(ids)

    def test_language_stratum_consistency(self, queries: list[dict]) -> None:
        mapping = {
            ("uk", "uk"): "ua_to_ua",
            ("en", "en"): "en_to_en",
            ("uk", "en"): "ua_to_en",
            ("en", "uk"): "en_to_ua",
        }
        for q in queries:
            expected = mapping.get((q["language"], q["target_language"]))
            assert q["stratum"] == expected, (
                f"stratum mismatch {q['query_id']}: ({q['language']}->{q['target_language']})"
            )


# ── Qrels (sparse) ────────────────────────────────────────────────────────


class TestQrelsSparse:
    def test_no_zero_relevance_entries(self, qrels: list[dict]) -> None:
        for qr in qrels:
            assert qr["relevance"] > 0, f"sparse violation: {qr['query_id']}/{qr['document_id']}"

    def test_no_no_answer_qrels(self, qrels: list[dict], query_ids: set[str]) -> None:
        na_qids = {qid for qid in query_ids if qid.startswith("QN")}
        for qr in qrels:
            assert qr["query_id"] not in na_qids, f"no-answer {qr['query_id']} has qrels"

    def test_no_duplicate_pairs(self, qrels: list[dict]) -> None:
        pairs = [(qr["query_id"], qr["document_id"]) for qr in qrels]
        assert len(set(pairs)) == len(pairs)

    def test_all_answerable_have_primary(self, qrels: list[dict], query_ids: set[str]) -> None:
        for qid in query_ids:
            if qid.startswith("QN"):
                continue
            primaries = [
                qr
                for qr in qrels
                if qr["query_id"] == qid
                and qr["relevance"] >= 2
                and not qr.get("distractor", False)
            ]
            assert len(primaries) >= 1, f"{qid}: no primary qrel"

    def test_all_doc_ids_in_corpus(self, qrels: list[dict], doc_ids: set[str]) -> None:
        for qr in qrels:
            assert qr["document_id"] in doc_ids, f"unknown doc: {qr['document_id']}"

    def test_all_query_ids_referenced(self, qrels: list[dict], query_ids: set[str]) -> None:
        qrel_qids = {qr["query_id"] for qr in qrels}
        answerable = {qid for qid in query_ids if not qid.startswith("QN")}
        missing = answerable - qrel_qids
        assert not missing, f"answerable queries missing from qrels: {missing}"

    def test_relevance_range(self, qrels: list[dict]) -> None:
        for qr in qrels:
            assert 0 <= qr["relevance"] <= 2

    def test_utility_range(self, qrels: list[dict]) -> None:
        for qr in qrels:
            assert -1.0 <= qr["utility"] <= 1.0

    def test_distractor_negative_utility(self, qrels: list[dict]) -> None:
        for qr in qrels:
            if qr.get("distractor", False):
                assert qr["utility"] < 0, f"distractor {qr['query_id']}/{qr['document_id']}"


# ── QDD distractor queries ────────────────────────────────────────────────


class TestQDDQueries:
    def test_each_qdd_has_primary_and_distractor(
        self, qrels: list[dict], query_ids: set[str]
    ) -> None:
        qdd_qids = {qid for qid in query_ids if qid.startswith("QDD")}
        for qid in qdd_qids:
            qid_qrels = [qr for qr in qrels if qr["query_id"] == qid]
            primaries = [qr for qr in qid_qrels if not qr.get("distractor", False)]
            distractors = [qr for qr in qid_qrels if qr.get("distractor", False)]
            assert len(primaries) >= 1, f"{qid}: no primary"
            assert len(distractors) >= 1, f"{qid}: no distractor"

    def test_qdd_distractor_relevance_ge2(self, qrels: list[dict], query_ids: set[str]) -> None:
        qdd_qids = {qid for qid in query_ids if qid.startswith("QDD")}
        for qid in qdd_qids:
            for qr in qrels:
                if qr["query_id"] == qid and qr.get("distractor", False):
                    assert qr["relevance"] >= 2, f"{qid}: distractor relevance={qr['relevance']}"


# ── Corpus ────────────────────────────────────────────────────────────────


class TestCorpus:
    def test_100_documents(self, manifest: dict) -> None:
        assert manifest["corpus"]["count"] == 100

    def test_all_files_have_dot_md(self, manifest: dict) -> None:
        for entry in manifest["corpus"]["files"]:
            did = entry["document_id"]
            assert did.endswith(".md"), f"document_id lacks .md: {did}"
            assert (DATASET_V1 / "corpus" / did).exists(), f"missing: {did}"

    def test_sha256_consistency(self, manifest: dict) -> None:
        for entry in manifest["corpus"]["files"]:
            path = DATASET_V1 / "corpus" / entry["document_id"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual == entry["sha256"], f"SHA256 mismatch for {entry['document_id']}"

    def test_no_duplicate_doc_ids(self, manifest: dict) -> None:
        doc_ids = [e["document_id"] for e in manifest["corpus"]["files"]]
        assert len(set(doc_ids)) == len(doc_ids)

    def test_language_from_suffix(self, manifest: dict) -> None:
        for entry in manifest["corpus"]["files"]:
            did = entry["document_id"]
            expected_lang = "uk" if did.endswith("-ua.md") else "en"
            assert entry["language"] == expected_lang, f"{did}: lang={entry['language']}"

    def test_hash_manifest_integrity(self, manifest: dict) -> None:
        corpus_text = json.dumps(manifest["corpus"]["files"], sort_keys=True)
        computed = hashlib.sha256(corpus_text.encode()).hexdigest()
        assert computed == manifest["corpus"]["hash_sha256"]


# ── Content support ────────────────────────────────────────────────────────


class TestContentSupport:
    def test_atomic_facts_in_primary_docs(
        self, qrels: list[dict], answers: list[dict], corpus: dict[str, str]
    ) -> None:
        for a in answers:
            if a["no_answer"]:
                continue
            qid = a["query_id"]
            primaries = [
                qr["document_id"]
                for qr in qrels
                if qr["query_id"] == qid
                and qr["relevance"] >= 2
                and not qr.get("distractor", False)
            ]
            assert len(primaries) >= 1, f"{qid}: no primary doc"
            for doc_id in primaries:
                content = corpus.get(doc_id, "")
                for fact in a.get("atomic_facts", []):
                    assert fact.lower() in content.lower(), f"{qid}: atomic fact not in {doc_id}"


# ── Absent topics ──────────────────────────────────────────────────────────


class TestAbsentTopics:
    def test_absent_tokens_not_in_corpus(self, corpus: dict[str, str]) -> None:
        all_text = " ".join(corpus.values()).lower()
        for token in ABSENT_TOKENS:
            assert token.lower() not in all_text, f"absent token '{token}' found in corpus"

    def test_no_answer_queries_reference_absent_topics(self, queries: list[dict]) -> None:
        for q in queries:
            if q["query_class"] != "no_answer":
                continue
            q_lower = q["query"].lower()
            has_absent = any(token.lower() in q_lower for token in ABSENT_TOKENS)
            assert has_absent, f"no-answer {q['query_id']} doesn't reference absent topic"


# ── Hash consistency ──────────────────────────────────────────────────────


class TestHashConsistency:
    def test_queries_hash(self, queries: list[dict], manifest: dict) -> None:
        computed = hashlib.sha256(
            json.dumps(queries, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        assert computed == manifest["queries"]["hash_sha256"]

    def test_qrels_hash(self, qrels: list[dict], manifest: dict) -> None:
        computed = hashlib.sha256(
            json.dumps(qrels, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        assert computed == manifest["qrels"]["hash_sha256"]

    def test_answers_hash(self, answers: list[dict], manifest: dict) -> None:
        computed = hashlib.sha256(
            json.dumps(answers, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        assert computed == manifest["expected_answers"]["hash_sha256"]


# ── Manifest structure ─────────────────────────────────────────────────────


class TestManifest:
    def test_schema_version(self, manifest: dict) -> None:
        assert manifest["schema_version"] == "3.1.0"

    def test_benchmark_version(self, manifest: dict) -> None:
        assert manifest["benchmark_version"] == "3.1.0"

    def test_generator_seed(self, manifest: dict) -> None:
        assert manifest["generator_seed"] == 42

    def test_generated_at_fixed(self, manifest: dict) -> None:
        generated_at = manifest["generated_at"]
        assert generated_at.endswith("+00:00")
        assert "T" in generated_at

    def test_annotation_type(self, manifest: dict) -> None:
        ann_type = manifest["qrels"]["annotation_type"]
        assert ann_type == "synthetic_deterministic"

    def test_scope_and_limitations(self, manifest: dict) -> None:
        limitations = manifest.get("scope_and_limitations", [])
        combined = " ".join(limitations).lower()
        assert "synthetic" in combined
        assert "not human" in combined

    def test_answerable_per_stratum_in_manifest(self, manifest: dict) -> None:
        ans = manifest["queries"]["answerable_per_stratum"]
        for s in STRATA:
            assert ans[s] >= 50, f"stratum {s}: {ans[s]} answerable"


# ── Expected answers ──────────────────────────────────────────────────────


class TestExpectedAnswers:
    def test_all_queries_have_answers(self, answers: list[dict], queries: list[dict]) -> None:
        qids = {q["query_id"] for q in queries}
        aid_qids = {a["query_id"] for a in answers}
        assert qids == aid_qids

    def test_no_answer_boolean(self, answers: list[dict]) -> None:
        for a in answers:
            assert isinstance(a["no_answer"], bool)

    def test_no_answer_has_no_citations(self, answers: list[dict]) -> None:
        for a in answers:
            if a["no_answer"]:
                assert len(a["citation_document_ids"]) == 0

    def test_answerable_has_citations(self, answers: list[dict]) -> None:
        for a in answers:
            if not a["no_answer"]:
                assert len(a.get("citation_document_ids", [])) >= 1

    def test_citation_ids_exist_in_corpus(self, answers: list[dict], doc_ids: set[str]) -> None:
        for a in answers:
            for cid in a.get("citation_document_ids", []):
                assert cid in doc_ids, f"answer {a['query_id']} cites unknown doc: {cid}"

    def test_citation_ids_are_primary_relevant(
        self, answers: list[dict], qrels: list[dict]
    ) -> None:
        primary_map: dict[str, set[str]] = {}
        for qr in qrels:
            if qr["relevance"] >= 2 and not qr.get("distractor", False):
                primary_map.setdefault(qr["query_id"], set()).add(qr["document_id"])
        for a in answers:
            if a["no_answer"]:
                continue
            for cid in a.get("citation_document_ids", []):
                assert cid in primary_map.get(a["query_id"], set()), (
                    f"answer {a['query_id']} cites non-primary doc: {cid}"
                )


# ── Byte-identical regeneration ──────────────────────────────────────────


class TestDeterministicRegeneration:
    def test_deterministic_queries(self, queries: list[dict], manifest: dict) -> None:
        computed = hashlib.sha256(
            json.dumps(queries, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        assert computed == manifest["queries"]["hash_sha256"]

    def test_deterministic_qrels(self, qrels: list[dict], manifest: dict) -> None:
        computed = hashlib.sha256(
            json.dumps(qrels, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        assert computed == manifest["qrels"]["hash_sha256"]

    def test_deterministic_answers(self, answers: list[dict], manifest: dict) -> None:
        computed = hashlib.sha256(
            json.dumps(answers, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        assert computed == manifest["expected_answers"]["hash_sha256"]
