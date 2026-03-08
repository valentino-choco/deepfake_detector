from __future__ import annotations

import argparse
import json
from pathlib import Path

from docfraud_layout import AnalysisConfig, analyze_document
from docfraud_layout.evaluation import classification_metrics, load_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark simple sur manifeste JSONL.")
    parser.add_argument("--manifest", required=True, help="Manifeste JSONL avec document_path et label")
    parser.add_argument("--output", default=None, help="Fichier JSON de sortie")
    parser.add_argument("--threshold", type=float, default=50.0, help="Seuil de suspicion sur le score de suspicion (100-authenticité)")
    args = parser.parse_args()

    rows = load_manifest(args.manifest)
    y_true = []
    y_score = []
    per_doc = []
    for row in rows:
        document_path = row["document_path"]
        label = int(row["label"])
        report = analyze_document(AnalysisConfig(document_path=document_path, doc_type_override=row.get("doc_type")))
        suspicion_score = 100.0 - report.score_layout
        y_true.append(label)
        y_score.append(suspicion_score / 100.0)
        per_doc.append({
            "document_path": document_path,
            "label": label,
            "authenticity_score": report.score_layout,
            "suspicion_score": suspicion_score,
            "top_anomaly": report.anomalies[0].description if report.anomalies else None,
        })

    metrics = classification_metrics(y_true, y_score, threshold=args.threshold / 100.0)
    payload = {"metrics": metrics, "documents": per_doc}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
