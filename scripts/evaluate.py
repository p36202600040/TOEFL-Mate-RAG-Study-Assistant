"""
scripts/evaluate.py — Jalankan pipeline evaluasi RAG.

Penggunaan:
    python scripts/evaluate.py
    python scripts/evaluate.py --top_k 3
    python scripts/evaluate.py --top_k 5 --output evaluation/results_k5.json

Hasil disimpan dengan nama unik, atau ke path --output yang belum ada.
"""
import sys
import json
import csv
import argparse
import uuid
from pathlib import Path
from datetime import datetime

# Tambahkan project root ke path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.evaluation import load_test_questions, run_evaluation


def save_results(summary: dict, json_path: Path, csv_path: Path):
    """Simpan hasil evaluasi ke JSON dan CSV."""
    # JSON
    with open(json_path, "x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"[Eval] Hasil JSON disimpan: {json_path}")

    # CSV
    results = summary.get("results", [])
    if results:
        fieldnames = []
        for row in results:
            for k in row.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
        with open(csv_path, "x", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in results:
                csv_row = {}
                for k in fieldnames:
                    v = row.get(k, "")
                    if isinstance(v, (list, dict)):
                        csv_row[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        csv_row[k] = v
                writer.writerow(csv_row)
        print(f"[Eval] Hasil CSV disimpan: {csv_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("RINGKASAN EVALUASI")
    print(f"{'='*60}")
    metrics = summary.get("metrics", {})
    for name, data in metrics.items():
        value = data.get("value", "N/A")
        n = data.get("n_samples", "?")
        if isinstance(value, float):
            print(f"  {name}: {value:.4f} (n={n})")
        else:
            print(f"  {name}: {value} (n={n})")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Evaluasi TOEFL Mate RAG")
    parser.add_argument("--top_k", type=int, default=None,
                        help="Override top_k untuk evaluasi")
    parser.add_argument("--dataset", type=str, default=None,
                        help="Path ke dataset pertanyaan uji")
    parser.add_argument("--output", type=str, default=None,
                        help="Path output JSON")
    parser.add_argument("--limit", type=int, default=None,
                        help="Batasi jumlah pertanyaan untuk preflight tanpa mengubah dataset")
    args = parser.parse_args()

    # Load dataset
    dataset_path = args.dataset or (config.EVALUATION_DIR / "test_questions.json")
    print(f"[Eval] Loading dataset: {dataset_path}")
    test_questions = load_test_questions(dataset_path)
    if args.limit is not None:
        if args.limit <= 0:
            parser.error("--limit harus lebih besar dari 0")
        test_questions = test_questions[:args.limit]
    print(f"[Eval] Loaded {len(test_questions)} pertanyaan")

    top_k = config.TOP_K if args.top_k is None else args.top_k
    if top_k <= 0:
        parser.error("--top_k harus lebih besar dari 0")
    if not test_questions:
        parser.error("Dataset evaluasi kosong")
    json_path = Path(args.output) if args.output else config.EVALUATION_DIR / f"results_{datetime.utcnow():%Y%m%dT%H%M%S}_{uuid.uuid4().hex[:8]}.json"
    csv_path = json_path.with_suffix(".csv")
    if json_path.exists() or csv_path.exists():
        parser.error("Output JSON atau CSV sudah ada; pilih nama lain")
    if not json_path.parent.is_dir() or json_path.suffix.lower() != ".json":
        parser.error("Direktori output harus ada dan output harus berformat .json")
    print(f"[Eval] Running with top_k={top_k}")

    # Run evaluation
    summary = run_evaluation(test_questions, top_k=top_k)

    # Save results
    save_results(summary, json_path, csv_path)


if __name__ == "__main__":
    main()
