"""
src/evaluation.py — Fungsi evaluasi metrik RAG.

Metrik yang dihitung:
- Recall@k: apakah chunk relevan muncul di top-k results
- Precision@k: jumlah chunk relevan di top-k / k
- Citation accuracy: sitasi halaman yang benar / total sitasi
- Out-of-scope handling: jawaban yang mengakui keterbatasan / total OOS
- Latency: waktu respons per pertanyaan

Metrik answer correctness dan groundedness memerlukan penilaian manusia
dan ditandai sesuai status.
"""
import re
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import config
from src.retriever import retrieve
from src.generator import generate_answer


def load_test_questions(path: str | Path | None = None) -> list[dict]:
    """Load dataset pertanyaan uji dari JSON."""
    p = Path(path or (config.EVALUATION_DIR / "test_questions.json"))
    if not p.exists():
        raise FileNotFoundError(f"Dataset evaluasi tidak ditemukan: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def compute_recall_at_k(
    retrieved_pages: list[int],
    relevant_pages: list[int],
    k: int = 5,
) -> float:
    """
    Recall@k: apakah setidaknya satu halaman relevan muncul di top-k.

    Definisi: 1.0 jika intersection(retrieved_pages[:k], relevant_pages) tidak kosong,
    0.0 jika kosong. Agregasi per query: rata-rata dari semua pertanyaan yang
    memiliki label relevant_pages.
    """
    if not relevant_pages:
        return 0.0  # Tidak bisa dihitung tanpa label
    top_k_pages = set(retrieved_pages[:k])
    relevant_set = set(relevant_pages)
    return 1.0 if top_k_pages & relevant_set else 0.0


def compute_precision_at_k(
    retrieved_pages: list[int],
    relevant_pages: list[int],
    k: int = 5,
) -> float:
    """
    Precision@k: jumlah halaman relevan di top-k / k.
    """
    if not relevant_pages:
        return 0.0
    top_k_pages = retrieved_pages[:k]
    relevant_set = set(relevant_pages)
    hits = sum(1 for p in top_k_pages if p in relevant_set)
    return hits / k


def extract_cited_pages(answer: str) -> list[int]:
    """Ekstrak nomor halaman dari sitasi [Halaman X] di jawaban."""
    # Pattern: [Halaman 123] atau [Page 123]
    pattern = r"\[(?:Halaman|Page)\s+(\d+)\]"
    matches = re.findall(pattern, answer, re.IGNORECASE)
    return [int(m) for m in matches]


def compute_citation_accuracy(
    cited_pages: list[int],
    relevant_pages: list[int],
) -> float:
    """
    Citation accuracy: sitasi halaman yang benar / total sitasi.
    Halaman "benar" jika ada dalam relevant_pages.
    """
    if not cited_pages:
        return 0.0  # Tidak ada sitasi
    if not relevant_pages:
        return 0.0  # Tidak bisa dihitung tanpa label
    relevant_set = set(relevant_pages)
    correct = sum(1 for p in cited_pages if p in relevant_set)
    return correct / len(cited_pages)


def check_out_of_scope(answer: str) -> bool:
    """
    Cek apakah jawaban mengakui bahwa informasi tidak ditemukan.
    Returns True jika jawaban mengandung pengakuan keterbatasan.
    """
    oos_indicators = [
        "tidak ditemukan",
        "tidak tersedia",
        "tidak ada dalam",
        "di luar cakupan",
        "tidak memiliki informasi",
        "not found",
        "not available",
        "outside the scope",
        "cannot find",
        "no information",
        "tidak dapat menemukan",
        "tidak mencakup",
        "tidak membahas",
        "belum tersedia",
    ]
    answer_lower = answer.lower()
    return any(ind in answer_lower for ind in oos_indicators)


def run_evaluation(
    test_questions: list[dict],
    top_k: int = 5,
    collection=None,
) -> dict:
    """
    Jalankan evaluasi lengkap.

    Args:
        test_questions: List of question dicts dari dataset
        top_k: Jumlah results yang diambil
        collection: ChromaDB collection (opsional)

    Returns:
        dict dengan semua hasil evaluasi
    """
    results = []
    total_recall = 0.0
    total_precision = 0.0
    total_citation_acc = 0.0
    recall_count = 0
    precision_count = 0
    citation_count = 0
    oos_correct = 0
    oos_total = 0
    latencies = []

    eval_config = {
        "top_k": top_k,
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "embedding_model": config.EMBEDDING_MODEL,
        "groq_model": config.GROQ_MODEL,
        "relevance_threshold": config.RELEVANCE_THRESHOLD,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    for item in test_questions:
        q_id = item.get("id", "unknown")
        question = item["question"]
        category = item.get("category", "unknown")
        relevant_pages = item.get("relevant_pages", [])
        expected_oos = category == "out_of_scope"

        print(f"[Eval] Processing {q_id}: {question[:60]}...")

        # Retrieval
        retrieved = retrieve(question, top_k=top_k, collection=collection)
        retrieved_pages = [r["page"] for r in retrieved]

        # Generation
        gen_result = generate_answer(question, retrieved)
        answer = gen_result["answer"]
        latency = gen_result["latency_seconds"]
        latencies.append(latency)

        # Metrics
        cited_pages = extract_cited_pages(answer)
        is_oos_response = check_out_of_scope(answer)

        result_item = {
            "id": q_id,
            "category": category,
            "question": question,
            "retrieved_pages": retrieved_pages,
            "retrieved_chunks": [r["chunk_id"] for r in retrieved],
            "retrieved_distances": [r["distance"] for r in retrieved],
            "answer": answer,
            "cited_pages": cited_pages,
            "latency_seconds": latency,
            "error": gen_result.get("error"),
        }

        # Recall & Precision (hanya jika ada label)
        if relevant_pages and not expected_oos:
            r_at_k = compute_recall_at_k(retrieved_pages, relevant_pages, top_k)
            p_at_k = compute_precision_at_k(retrieved_pages, relevant_pages, top_k)
            c_acc = compute_citation_accuracy(cited_pages, relevant_pages)

            result_item["recall_at_k"] = r_at_k
            result_item["precision_at_k"] = p_at_k
            result_item["citation_accuracy"] = c_acc

            total_recall += r_at_k
            total_precision += p_at_k
            recall_count += 1
            precision_count += 1

            if cited_pages:
                total_citation_acc += c_acc
                citation_count += 1

        # Out-of-scope
        if expected_oos:
            oos_total += 1
            if answer and is_oos_response:
                oos_correct += 1
                result_item["oos_handled_correctly"] = True
            elif not answer:
                result_item["oos_handled_correctly"] = "NOT_RUN_NO_API_KEY"
            else:
                result_item["oos_handled_correctly"] = False

        # Human evaluation fields (to be filled manually)
        result_item["answer_correctness"] = "NOT_RATED"
        result_item["groundedness"] = "NOT_RATED"
        result_item["human_notes"] = ""

        results.append(result_item)

    # Aggregate metrics
    has_generation = any(bool(r.get("answer")) for r in results)
    avg_recall = total_recall / recall_count if recall_count > 0 else 0.0
    avg_precision = total_precision / precision_count if precision_count > 0 else 0.0
    avg_citation = (total_citation_acc / citation_count) if (citation_count > 0 and has_generation) else ("REQUIRES_GROQ_API_KEY" if not has_generation else 0.0)
    oos_rate = (oos_correct / oos_total) if (oos_total > 0 and has_generation) else ("REQUIRES_GROQ_API_KEY" if not has_generation else 0.0)
    avg_latency = (sum(latencies) / len(latencies)) if (latencies and has_generation) else ("REQUIRES_GROQ_API_KEY" if not has_generation else 0.0)

    summary = {
        "config": eval_config,
        "metrics": {
            "recall_at_k": {"value": avg_recall, "n_samples": recall_count,
                           "definition": "Fraction of queries where at least one relevant page appeared in top-k results"},
            "precision_at_k": {"value": avg_precision, "n_samples": precision_count,
                              "definition": "Average (relevant pages in top-k / k)"},
            "citation_accuracy": {"value": avg_citation, "n_samples": citation_count,
                                 "definition": "Correct cited pages / total cited pages"},
            "out_of_scope_handling": {"value": oos_rate, "n_samples": oos_total,
                                     "definition": "OOS questions correctly acknowledged / total OOS questions"},
            "avg_latency_seconds": {"value": avg_latency, "n_samples": len(latencies),
                                   "definition": "Average response time per question (seconds)"},
            "answer_correctness": {"value": "REQUIRES_HUMAN_REVIEW",
                                  "definition": "Fraction of answers matching reference answer rubric (manual)"},
            "groundedness": {"value": "REQUIRES_HUMAN_REVIEW",
                            "definition": "Fraction of factual claims supported by retrieved context (manual)"},
        },
        "results": results,
    }

    return summary

