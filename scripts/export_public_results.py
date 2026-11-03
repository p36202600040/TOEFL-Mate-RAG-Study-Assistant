"""Ekspor artefak V2 tanpa pesan error mentah; sumber asli tidak diubah."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    destination = ROOT / "evaluation/public"
    destination.mkdir(exist_ok=True)
    for k in (5, 3):
        source = ROOT / f"evaluation/results_v2_k{k}.json"
        output = destination / source.name
        if output.exists():
            raise FileExistsError(f"Output sudah ada: {output}")
        data = json.loads(source.read_text(encoding="utf-8"))
        for row in data["results"]:
            if row.get("error"):
                row["error"] = "GENERATION_FAILED: detail provider dihapus untuk publikasi."
        data["publication_note"] = "Salinan publik tersanitasi; bukan run baru. Pesan error provider dihapus, metrik historis tidak dihitung ulang."
        with output.open("x", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(output)


if __name__ == "__main__":
    main()
