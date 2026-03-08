from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Dict, List, Tuple

from .geometry import cluster_values
from .reference_data import REFERENCE_LAYOUTS
from .schemas import BBoxElement, LayoutAnomaly


def analyze_alignment_consistency(
    elements: List[BBoxElement],
    page_w: int,
    page_h: int,
    doc_type: str,
    tolerance_px: int = 15,
) -> Tuple[Dict, List[LayoutAnomaly]]:
    if len(elements) < 5:
        return {}, []

    anomalies: List[LayoutAnomaly] = []
    x_positions = sorted(set(element.x_min for element in elements if element.text.strip()))
    columns = cluster_values(x_positions, tolerance=tolerance_px, min_cluster_size=2)

    misaligned = []
    for element in elements:
        if not columns:
            break
        best_column = min(columns, key=lambda column: abs(element.x_min - column))
        offset = abs(element.x_min - best_column)
        if 3 < offset <= 25:
            misaligned.append({"text": element.text[:40], "offset": offset, "y": element.y_min})
    ratio = len(misaligned) / max(1, len(elements))
    if ratio > 0.15:
        anomalies.append(LayoutAnomaly(
            categorie="alignement_global",
            severite="warning",
            description=f"{len(misaligned)} éléments ({ratio:.0%}) sont désalignés par rapport aux colonnes dominantes.",
            score_impact=5.0,
        ))

    row_map: Dict[int, List[BBoxElement]] = defaultdict(list)
    for element in elements:
        row_key = int(round(element.center_y / 12.0))
        row_map[row_key].append(element)

    row_offsets = []
    for row_elements in row_map.values():
        if len(row_elements) < 2:
            continue
        row_x = sorted(element.x_min for element in row_elements)
        median_x = statistics.median(row_x)
        for value in row_x:
            row_offsets.append(abs(value - median_x))

    row_offset_median = round(statistics.median(row_offsets), 2) if row_offsets else 0.0

    section_metrics = {}
    ref = REFERENCE_LAYOUTS.get(doc_type)
    if ref and page_h > 0:
        for section_def in ref["sections_attendues"]:
            name = section_def["nom"]
            y_lo = section_def["zone_y"][0] * page_h
            y_hi = section_def["zone_y"][1] * page_h
            section_elements = [element for element in elements if y_lo <= element.center_y <= y_hi]
            if len(section_elements) < 3:
                continue
            section_cols = cluster_values(sorted(set(element.x_min for element in section_elements)), tolerance=tolerance_px, min_cluster_size=2)
            local_misaligned = 0
            for element in section_elements:
                if not section_cols:
                    break
                best_column = min(section_cols, key=lambda column: abs(element.x_min - column))
                if 3 < abs(element.x_min - best_column) <= 25:
                    local_misaligned += 1
            local_ratio = local_misaligned / max(1, len(section_elements))
            section_metrics[name] = {
                "nb_elements": len(section_elements),
                "nb_colonnes": len(section_cols),
                "ratio_desalignes": round(local_ratio, 3),
            }
            if local_ratio > 0.20:
                anomalies.append(LayoutAnomaly(
                    categorie="alignement_section",
                    severite="warning",
                    description=f"La section '{name}' présente {local_ratio:.0%} d'éléments désalignés.",
                    zone=name,
                    score_impact=4.0,
                ))

    return {
        "colonnes": columns,
        "nb_colonnes": len(columns),
        "ratio_desalignes": round(ratio, 3),
        "row_offset_median_px": row_offset_median,
        "section_metrics": section_metrics,
    }, anomalies


def analyze_spacing_consistency(elements: List[BBoxElement]) -> Tuple[Dict, List[LayoutAnomaly]]:
    if len(elements) < 10:
        return {}, []
    anomalies: List[LayoutAnomaly] = []
    sorted_elements = sorted(elements, key=lambda element: (element.y_min, element.x_min))
    gaps = [
        sorted_elements[index].y_min - sorted_elements[index - 1].y_max
        for index in range(1, len(sorted_elements))
    ]
    gaps = [gap for gap in gaps if 0 < gap < 200]
    if not gaps:
        return {}, []

    median_gap = statistics.median(gaps)
    std_gap = statistics.stdev(gaps) if len(gaps) > 2 else 0.0
    irregular = [gap for gap in gaps if std_gap > 0 and abs(gap - median_gap) > 3 * std_gap]
    if len(irregular) > max(3, int(len(gaps) * 0.1)):
        anomalies.append(LayoutAnomaly(
            categorie="espacement_irregulier",
            severite="warning",
            description=(
                f"{len(irregular)} interlignes sont anormaux (médiane={median_gap:.1f}px, σ={std_gap:.1f}px)."
            ),
            score_impact=4.0,
        ))
    return {
        "median_gap_px": round(median_gap, 2),
        "std_gap_px": round(std_gap, 2),
        "nb_irregular_gaps": len(irregular),
    }, anomalies
