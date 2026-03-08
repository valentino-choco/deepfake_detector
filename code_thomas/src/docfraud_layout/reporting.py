from __future__ import annotations

import json
from pathlib import Path

from .schemas import AnalysisReport


def report_to_console(report: AnalysisReport) -> str:
    lines = [
        "=== ANALYSE DE FRAUDE DOCUMENTAIRE ===",
        f"Type document : {report.type_document}",
        f"Source        : {report.source_kind}",
        f"Pages         : {report.nb_pages}",
        f"Éléments OCR  : {report.nb_elements_ocr}",
        f"Score brut    : {report.score_layout_raw:.2f}/100",
        f"Score calibré : {report.score_layout:.2f}/100",
        "",
        "Sections manquantes : " + (", ".join(report.sections_manquantes) if report.sections_manquantes else "aucune"),
        "",
        "Top candidats :",
    ]
    if report.candidates:
        for candidate in report.candidates[:10]:
            lines.append(
                f"  - {candidate.candidate_id} | {candidate.text} | p.{candidate.page_id + 1} | "
                f"{candidate.verdict} | raw={candidate.raw_score:.3f} | cal={candidate.calibrated_score:.3f}"
            )
    else:
        lines.append("  - aucun candidat numérique détecté")

    if report.anomalies:
        lines.append("")
        lines.append("Anomalies :")
        for anomaly in report.anomalies:
            lines.append(
                f"  - [{anomaly.severite}] {anomaly.categorie} | impact={anomaly.score_impact:.1f} | {anomaly.description}"
            )
    return "\n".join(lines)


def write_json_report(report: AnalysisReport, output_path: str | Path) -> None:
    Path(output_path).write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
