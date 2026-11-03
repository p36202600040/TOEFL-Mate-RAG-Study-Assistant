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
import unicodedata
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import config
from src.retriever import retrieve
from src.generator import generate_answer


def source_page_pairs(items):
    """Pasangan eksplisit saja; label halaman lama tidak menyiratkan sumber."""
    return {(normalize_source(item["source"]), int(item["page"]))
            for item in items if item.get("source") and item.get("page") is not None}


def normalize_source(value):
    return "".join(ch for ch in unicodedata.normalize("NFKC", str(value or "")) if unicodedata.category(ch) != "Cf").strip()


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


def extract_citations(answer: str) -> list[dict]:
    """Ekstrak sitasi kanonis dan variasi lama setelah normalisasi Unicode.

    Sitasi tanpa source tetap dipertahankan dengan source=None dan tidak boleh
    dianggap valid otomatis pada koleksi multi-dokumen.
    """
    normalized = unicodedata.normalize("NFKC", answer or "")
    normalized = normalized.replace("【", "[").replace("】", "]")
    canonical = re.compile(r"\[\s*([^\[\],]+?\.pdf)\s*,\s*(?:Halaman|Page)\s+(\d+)\s*\]", re.I)
    simple = re.compile(r"\[\s*(?:Halaman|Page)\s+(\d+)\s*\]", re.I)
    citations = [{"source": source.strip(), "page": int(page)} for source, page in canonical.findall(normalized)]
    canonical_spans = [match.span() for match in canonical.finditer(normalized)]
    for match in simple.finditer(normalized):
        if not any(start <= match.start() < end for start, end in canonical_spans):
            citations.append({"source": None, "page": int(match.group(1))})
    return citations


def extract_cited_pages(answer: str) -> list[int]:
    """Kompatibilitas mundur: kembalikan halaman dari semua sitasi yang terbaca."""
    return [citation["page"] for citation in extract_citations(answer)]


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


def validate_citations_against_contexts(citations: list[dict], contexts: list[dict]) -> list[dict]:
    """Tandai apakah source-halaman sitasi ada pada konteks retrieval aktual."""
    available = {(normalize_source(ctx.get("source")), int(ctx.get("page", 0))) for ctx in contexts}
    source_count = len({source for source, _ in available})
    validated = []
    for citation in citations:
        source, page = citation.get("source"), citation["page"]
        valid = (normalize_source(source), page) in available if source else source_count == 1 and any(p == page for _, p in available)
        validated.append({**citation, "in_retrieved_context": valid})
    return validated


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
    if not test_questions:
        raise ValueError("Dataset evaluasi kosong.")
    config.validate_settings()
    results = []
    total_recall = 0.0
    total_precision = 0.0
    recall_count = 0
    precision_count = 0
    citation_total = 0
    citation_correct = 0
    citation_coverage_count = 0
    coverage_total = 0
    location_total = 0
    location_correct = 0
    oos_correct = 0
    oos_total = 0
    retrieval_latencies = []
    generation_latencies = []
    end_to_end_latencies = []
    run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:6]}"

    eval_config = {
        "top_k": top_k,
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "embedding_model": config.EMBEDDING_MODEL,
        "groq_model": config.GROQ_MODEL,
        "relevance_threshold": config.RELEVANCE_THRESHOLD,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "dataset_sha256": hashlib.sha256(json.dumps(test_questions, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "dataset_items": len(test_questions),
        "collection": getattr(collection, "name", None) or config.CHROMA_COLLECTION,
        "embedding_dimension": "UNKNOWN",
        "index_manifest": "UNKNOWN",
        "query_enrichment_version": "indonesian-terms-v1",
        "generation_max_tokens": config.GROQ_MAX_TOKENS,
        "generation_temperature": config.GROQ_TEMPERATURE,
        "prompt_version": "canonical-source-page-citations-v2",
    }

    for item in test_questions:
        q_id = item.get("id", "unknown")
        question = item["question"]
        category = item.get("category", "unknown")
        relevant_pages = item.get("relevant_pages", [])
        expected_oos = category == "out_of_scope"

        print(f"[Eval] Processing {q_id}: {question[:60]}...")

        item_start = time.perf_counter()
        retrieval_start = time.perf_counter()
        try:
            retrieved = retrieve(question, top_k=top_k, collection=collection)
            retrieval_error = None
        except Exception as error:
            retrieved = []
            retrieval_error = f"Retrieval gagal: {type(error).__name__}"
        retrieval_latency = round(time.perf_counter() - retrieval_start, 3)
        retrieved_pages = [r["page"] for r in retrieved]

        # Generation tidak dijalankan apabila retrieval sudah gagal.
        gen_result = (generate_answer(question, retrieved) if retrieval_error is None else {
            "answer": "", "model": config.GROQ_MODEL, "latency_seconds": 0.0,
            "error": retrieval_error,
        })
        answer = gen_result["answer"]
        generation_latency = gen_result["latency_seconds"]
        end_to_end_latency = round(time.perf_counter() - item_start, 3)
        retrieval_latencies.append(retrieval_latency)
        if answer:
            generation_latencies.append(generation_latency)
            end_to_end_latencies.append(end_to_end_latency)

        # Metrics
        citations = validate_citations_against_contexts(extract_citations(answer), retrieved)
        cited_pages = [citation["page"] for citation in citations]
        is_oos_response = check_out_of_scope(answer)

        result_item = {
            "id": q_id,
            "category": category,
            "question": question,
            "retrieved_pages": retrieved_pages,
            "retrieved_contexts": [{"source": r.get("source"), "page": r.get("page"), "chunk_id": r.get("chunk_id"), "distance": r.get("distance")} for r in retrieved],
            "retrieved_chunks": [r["chunk_id"] for r in retrieved],
            "retrieved_distances": [r["distance"] for r in retrieved],
            "answer": answer,
            "cited_pages": cited_pages,
            "citations": citations,
            "retrieval_latency_seconds": retrieval_latency,
            "generation_latency_seconds": generation_latency,
            "end_to_end_latency_seconds": end_to_end_latency,
            "latency_seconds": generation_latency,
            "error": gen_result.get("error"),
            "status": "SUCCESS" if answer else ("RETRIEVAL_FAILED" if retrieval_error else "GENERATION_FAILED"),
            "retrieval_status": "FAILED" if retrieval_error else "SUCCESS",
            "generation_status": "NOT_RUN" if retrieval_error else ("SUCCESS" if answer else "FAILED"),
            "effective_model": gen_result.get("model") if not retrieval_error else None,
        }

        labels = source_page_pairs(item.get("relevant_sources", []))
        result_item["label_status"] = "SOURCE_PAGE" if labels else ("SOURCE_UNKNOWN" if relevant_pages else "UNLABELED")
        if answer and not expected_oos:
            coverage_total += 1
            citation_coverage_count += bool(citations)
        location_total += len(citations)
        location_correct += sum(c["in_retrieved_context"] for c in citations)

        # Jangan menganggap label historis berbasis halaman memiliki sumber tertentu.
        if labels and not expected_oos and not retrieval_error:
            hits = [bool(source_page_pairs([r]) & labels) for r in retrieved[:top_k]]
            r_at_k = float(any(hits))
            p_at_k = sum(hits) / top_k
            matches = [bool(source_page_pairs([c]) & labels) for c in citations]
            c_acc = sum(matches) / len(matches) if matches else None

            result_item["recall_at_k"] = r_at_k
            result_item["precision_at_k"] = p_at_k
            result_item["citation_accuracy"] = c_acc

            total_recall += r_at_k
            total_precision += p_at_k
            recall_count += 1
            precision_count += 1

            if cited_pages:
                citation_total += len(cited_pages)
                citation_correct += sum(matches)

        # Out-of-scope
        if expected_oos:
            oos_total += 1
            if answer and is_oos_response:
                oos_correct += 1
                result_item["oos_refusal_phrase_detected"] = True
            elif not answer:
                result_item["oos_refusal_phrase_detected"] = "NOT_RUN"
            else:
                result_item["oos_refusal_phrase_detected"] = False
            result_item["oos_human_review"] = "NOT_RATED"

        # Human evaluation fields (to be filled manually)
        result_item["answer_correctness"] = "NOT_RATED"
        result_item["groundedness"] = "NOT_RATED"
        result_item["human_notes"] = ""

        results.append(result_item)

    # Aggregate metrics
    has_generation = any(bool(r.get("answer")) for r in results)
    avg_recall = total_recall / recall_count if recall_count > 0 else "NO_SOURCE_LABELS"
    avg_precision = total_precision / precision_count if precision_count > 0 else "NO_SOURCE_LABELS"
    avg_citation = (citation_correct / citation_total) if citation_total else ("NOT_RUN" if not has_generation else "NO_LABELED_CITATIONS")
    oos_rate = (oos_correct / oos_total) if (oos_total > 0 and has_generation) else ("REQUIRES_GROQ_API_KEY" if not has_generation else 0.0)
    avg_latency = (sum(generation_latencies) / len(generation_latencies)) if generation_latencies else ("NOT_RUN" if not has_generation else 0.0)

    summary = {
        "config": eval_config,
        "metrics": {
            "recall_at_k": {"value": avg_recall, "n_samples": recall_count,
                           "definition": "Hit@k: fraction of successfully retrieved queries with explicit source-page labels and a matching chunk"},
            "precision_at_k": {"value": avg_precision, "n_samples": precision_count,
                              "definition": "Mean matching source-page chunks / k; duplicate chunks count separately; failed retrieval excluded"},
            "citation_accuracy_micro": {"value": avg_citation, "n_samples": citation_total,
                                 "definition": "Citations matching explicit source-page labels / citations for source-labeled items; not claim support"},
            "citation_location_validity": {"value": location_correct / location_total if location_total else "NO_CITATIONS", "n_samples": location_total, "definition": "Citations located in retrieved contexts; not claim support"},
            "citation_coverage": {"value": citation_coverage_count / coverage_total if coverage_total else "NOT_RUN",
                                 "n_samples": coverage_total, "definition": "Successful in-scope answers with a parseable citation / successful in-scope answers"},
            "oos_refusal_phrase_indicator": {"value": oos_rate, "n_samples": oos_total,
                                     "definition": "OOS items containing an indicative phrase / all OOS items, including failed generation; not OOS accuracy"},
            "avg_generation_latency_seconds": {"value": avg_latency, "n_samples": len(generation_latencies),
                                    "definition": "Average Groq generation latency for successful answers (seconds)"},
            "avg_retrieval_latency_seconds": {"value": sum(retrieval_latencies) / len(retrieval_latencies) if retrieval_latencies else 0.0, "n_samples": len(retrieval_latencies),
                                    "definition": "Average local retrieval latency, may include cold embedding load"},
            "avg_end_to_end_latency_seconds": {"value": sum(end_to_end_latencies) / len(end_to_end_latencies) if end_to_end_latencies else "NOT_RUN", "n_samples": len(end_to_end_latencies),
                                    "definition": "Average retrieval-to-answer latency for successful answers (seconds)"},
            "answer_correctness": {"value": "REQUIRES_HUMAN_REVIEW",
                                  "definition": "Fraction of answers matching reference answer rubric (manual)"},
            "groundedness": {"value": "REQUIRES_HUMAN_REVIEW",
                            "definition": "Fraction of factual claims supported by retrieved context (manual)"},
        },
        "results": results,
        "run_status": "COMPLETE" if all(r["status"] == "SUCCESS" for r in results) else "PARTIAL_OR_NOT_RUN",
    }

    return summary
