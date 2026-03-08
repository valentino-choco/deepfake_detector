from __future__ import annotations

from .config import AnalysisConfig


def calibrate_candidate_score(raw_score: float, doc_type: str, source_kind: str) -> float:
    doc_bias = {
        "ticket_caisse": -0.03,
        "facture": 0.00,
        "releve_bancaire": 0.04,
        "contrat": 0.02,
        "formulaire": 0.01,
        "unknown": 0.00,
    }.get(doc_type, 0.0)
    source_bias = {
        "native_pdf": -0.02,
        "ocr_scan": 0.03,
        "image": 0.05,
        "json_ocr": 0.00,
        "unknown": 0.00,
    }.get(source_kind, 0.0)
    return round(min(1.0, max(0.0, raw_score + doc_bias + source_bias)), 4)


def verdict_from_candidate_score(score: float, threshold: float = 0.55) -> str:
    if score >= max(0.8, threshold + 0.2):
        return "high_risk"
    if score >= threshold:
        return "review"
    return "ok"


def calibrate_authenticity_score(raw_score: float, doc_type: str, source_kind: str, config: AnalysisConfig) -> float:
    doc_bias = config.authenticity_bias_points_by_doc_type.get(doc_type, 0.0)
    source_bias = config.authenticity_bias_points_by_source.get(source_kind, 0.0)
    return round(min(100.0, max(0.0, raw_score + doc_bias + source_bias)), 2)
