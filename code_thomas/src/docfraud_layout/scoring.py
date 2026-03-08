from __future__ import annotations

from typing import Iterable, List

from .calibration import calibrate_authenticity_score
from .config import AnalysisConfig
from .schemas import CandidateScore, LayoutAnomaly


def compute_layout_scores(
    anomalies: Iterable[LayoutAnomaly],
    candidate_scores: List[CandidateScore],
    doc_type: str,
    source_kind: str,
    config: AnalysisConfig,
) -> tuple[float, float]:
    deduction = sum(anomaly.score_impact for anomaly in anomalies)
    risky_candidates = [candidate for candidate in candidate_scores if candidate.verdict in {"review", "high_risk"}]
    candidate_penalty = sum(candidate.calibrated_score for candidate in risky_candidates[:5]) * 8.0
    raw_score = max(0.0, 100.0 - deduction - candidate_penalty)
    calibrated = calibrate_authenticity_score(raw_score, doc_type, source_kind, config)
    return round(raw_score, 2), round(calibrated, 2)
