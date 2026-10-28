"""
scripts/evaluate.py — Jalankan pipeline evaluasi RAG.

Penggunaan:
    python scripts/evaluate.py
    python scripts/evaluate.py --top_k 3
    python scripts/evaluate.py --top_k 5 --output evaluation/results_k5.json

Hasil disimpan ke evaluation/results.json dan evaluation/results.csv
"""
import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime

# Tambahkan project root ke path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.evaluation import load_test_questions, run_evaluation


def save_results(summary: dict, json_path: Path, csv_path: Path):
    """Simpan hasil evaluasi ke JSON dan CSV."""
    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
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
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
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
    args = parser.parse_args()

    # Load dataset
    dataset_path = args.dataset or (config.EVALUATION_DIR / "test_questions.json")
    print(f"[Eval] Loading dataset: {dataset_path}")
    test_questions = load_test_questions(dataset_path)
    print(f"[Eval] Loaded {len(test_questions)} pertanyaan")

    top_k = args.top_k or config.TOP_K
    print(f"[Eval] Running with top_k={top_k}")

    # Run evaluation
    summary = run_evaluation(test_questions, top_k=top_k)

    # Save results
    json_path = Path(args.output) if args.output else (config.EVALUATION_DIR / "results.json")
    csv_path = json_path.with_suffix(".csv")
    save_results(summary, json_path, csv_path)


if __name__ == "__main__":
    main()

