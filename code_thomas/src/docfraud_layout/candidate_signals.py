from __future__ import annotations

from statistics import mean
from typing import Dict, Iterable, List

from .schemas import BBoxElement, CandidateRegion


def _neighbor_elements(elements: Iterable[BBoxElement], candidate: CandidateRegion, margin_y: int = 24) -> List[BBoxElement]:
    x0, y0, x1, y1 = candidate.bbox
    neighbors = []
    for element in elements:
        if element.page_id != candidate.page_id:
            continue
        vertical_overlap = not (element.y_max < y0 - margin_y or element.y_min > y1 + margin_y)
        if vertical_overlap:
            neighbors.append(element)
    return neighbors


def compute_candidate_signals(candidate: CandidateRegion, elements: List[BBoxElement]) -> Dict[str, float]:
    neighbors = _neighbor_elements(elements, candidate)

    x_positions = [element.x_min for element in neighbors if element.text]
    local_alignment_break = 0.0
    if len(x_positions) >= 3:
        local_mean = mean(x_positions)
        local_alignment_break = min(1.0, abs(candidate.bbox[0] - local_mean) / 120.0)

    fonts = [element.font_name for element in neighbors if element.font_name]
    dominant_font_ratio = 1.0
    if fonts:
        counts = {font: fonts.count(font) for font in set(fonts)}
        dominant_font_ratio = max(counts.values()) / max(1, len(fonts))
    font_inconsistency = 1.0 - dominant_font_ratio

    numeric_neighbors = sum(any(ch.isdigit() for ch in element.text) for element in neighbors)
    numeric_context_ratio = numeric_neighbors / max(1, len(neighbors))
    isolated_numeric_value = 1.0 - numeric_context_ratio

    text_len = len(candidate.text.replace(" ", ""))
    unusual_length = 0.0
    if candidate.candidate_type == "amount" and text_len > 12:
        unusual_length = 0.7
    elif candidate.candidate_type == "long_numeric" and text_len > 14:
        unusual_length = 0.6
    elif candidate.candidate_type == "date" and text_len not in {8, 10}:
        unusual_length = 0.4

    return {
        "local_alignment_break": round(local_alignment_break, 4),
        "font_inconsistency": round(font_inconsistency, 4),
        "isolated_numeric_value": round(isolated_numeric_value, 4),
        "unusual_length": round(unusual_length, 4),
    }


def aggregate_candidate_signals(signals: Dict[str, float]) -> float:
    weights = {
        "local_alignment_break": 0.35,
        "font_inconsistency": 0.25,
        "isolated_numeric_value": 0.20,
        "unusual_length": 0.20,
    }
    score = sum(signals.get(key, 0.0) * weight for key, weight in weights.items())
    return round(min(1.0, max(0.0, score)), 4)
