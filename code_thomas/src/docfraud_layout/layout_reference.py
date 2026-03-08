from __future__ import annotations

import statistics
from typing import Dict, List, Tuple

from .reference_data import FIELD_EXPECTED_ZONES, REFERENCE_LAYOUTS
from .schemas import BBoxElement, LayoutAnomaly


def analyze_reference_sections(
    elements: List[BBoxElement],
    doc_type: str,
    page_h: int,
    keyword_min_hits: int = 1,
) -> Tuple[Dict, List[str], List[LayoutAnomaly]]:
    ref = REFERENCE_LAYOUTS.get(doc_type)
    if not ref or page_h <= 0:
        return {}, [], []

    sections: Dict[str, Dict] = {}
    anomalies: List[LayoutAnomaly] = []
    observed_sequence = []

    for index, section_def in enumerate(ref["sections_attendues"]):
        name = section_def["nom"]
        y_lo = section_def["zone_y"][0] * page_h
        y_hi = section_def["zone_y"][1] * page_h
        keywords = [keyword.lower() for keyword in ref["keywords_sections"].get(name, [])]
        zone_elements = [element for element in elements if y_lo <= element.center_y <= y_hi]
        zone_text = " ".join(element.text.lower() for element in zone_elements)
        matches = [keyword for keyword in keywords if keyword in zone_text]
        present = len(matches) >= keyword_min_hits or (not keywords and len(zone_elements) >= 2)
        observed_y = round(statistics.median([element.center_y for element in zone_elements]), 1) if zone_elements else None
        sections[name] = {
            "present": present,
            "obligatoire": section_def["obligatoire"],
            "zone_y_attendue": list(section_def["zone_y"]),
            "keywords_trouves": matches,
            "nb_elements_zone": len(zone_elements),
            "observed_center_y": observed_y,
        }
        if present and observed_y is not None:
            observed_sequence.append((index, name, observed_y))

    missing = [
        name
        for name, details in sections.items()
        if details["obligatoire"] and not details["present"]
    ]
    for missing_name in missing:
        anomalies.append(LayoutAnomaly(
            categorie="section_manquante",
            severite="critical",
            description=f"Section obligatoire '{missing_name}' non détectée dans la zone attendue.",
            zone=missing_name,
            score_impact=10.0,
        ))

    for previous, current in zip(observed_sequence, observed_sequence[1:]):
        _, prev_name, prev_y = previous
        _, current_name, current_y = current
        if current_y + 5 < prev_y:
            anomalies.append(LayoutAnomaly(
                categorie="ordre_sections",
                severite="warning",
                description=(
                    f"L'ordre observé des sections semble inversé : '{current_name}' "
                    f"apparaît visuellement avant '{prev_name}'."
                ),
                zone=f"{prev_name}->{current_name}",
                score_impact=5.0,
            ))

    coverage = round(
        sum(1 for details in sections.values() if details["present"]) / max(1, len(sections)),
        3,
    )
    metrics = {
        "coverage": coverage,
        "sections": sections,
        "missing_sections": missing,
    }
    return metrics, missing, anomalies


def analyze_field_positions(elements: List[BBoxElement], doc_type: str, page_h: int) -> Tuple[Dict, List[LayoutAnomaly]]:
    anomalies: List[LayoutAnomaly] = []
    field_zones = FIELD_EXPECTED_ZONES.get(doc_type, {})
    if not field_zones or page_h <= 0:
        return {"field_matches": {}}, []

    field_matches: Dict[str, int] = {key: 0 for key in field_zones}
    for element in elements:
        text = element.text.lower().strip()
        if len(text) < 2:
            continue
        y_norm = element.center_y / page_h
        for keyword, (y_lo, y_hi) in field_zones.items():
            if keyword in text:
                field_matches[keyword] += 1
                if not (y_lo <= y_norm <= y_hi):
                    anomalies.append(LayoutAnomaly(
                        categorie="champ_mal_positionne",
                        severite="warning",
                        description=(
                            f"Champ '{keyword}' détecté à y={y_norm:.2f} "
                            f"hors de la zone attendue [{y_lo:.2f}, {y_hi:.2f}] ; "
                            f"texte='{element.text[:60]}'."
                        ),
                        zone=f"page_{element.page_id + 1}",
                        position={"y_norm": round(y_norm, 3), "expected": [y_lo, y_hi]},
                        score_impact=6.0,
                    ))
                break

    return {"field_matches": field_matches}, anomalies
