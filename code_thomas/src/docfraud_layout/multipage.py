from __future__ import annotations

import statistics
from typing import Dict, List, Tuple

import cv2
import numpy as np

from .geometry import group_elements_by_page
from .schemas import DocumentPayload, LayoutAnomaly
from .visual_layout import compute_ela, detect_graphic_zones, pil_to_bgr


def _token_signature(elements, page_h: int, lower: float, upper: float) -> set[str]:
    tokens = set()
    if page_h <= 0:
        return tokens
    for element in elements:
        y_norm = element.center_y / page_h
        if lower <= y_norm <= upper:
            for token in element.text.lower().split():
                if len(token) > 2:
                    tokens.add(token)
    return tokens


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def analyze_multipage_consistency(payload: DocumentPayload, doc_type: str) -> Tuple[Dict, List[LayoutAnomaly]]:
    if payload.page_count < 2:
        return {"nb_pages": payload.page_count, "note": "document mono-page"}, []

    anomalies: List[LayoutAnomaly] = []
    metrics: Dict = {"nb_pages": payload.page_count, "page_stats": []}

    # visual consistency when images exist
    if payload.images:
        lap_values = []
        ela_values = []
        brightness_values = []
        for page_idx, image in enumerate(payload.images):
            image_bgr = pil_to_bgr(image)
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            ela = compute_ela(image_bgr)
            brightness = float(np.mean(gray))
            lap_values.append(lap_var)
            ela_values.append(ela)
            brightness_values.append(brightness)
            metrics["page_stats"].append({
                "page": page_idx + 1,
                "laplacian_var": round(lap_var, 2),
                "ela": round(ela, 2),
                "brightness": round(brightness, 1),
            })

        lap_median = statistics.median(lap_values)
        ela_median = statistics.median(ela_values)
        bright_median = statistics.median(brightness_values)
        lap_std = statistics.stdev(lap_values) if len(lap_values) > 2 else 0.0
        ela_std = statistics.stdev(ela_values) if len(ela_values) > 2 else 0.0

        for page in metrics["page_stats"]:
            reasons = []
            if lap_std > 0 and abs(page["laplacian_var"] - lap_median) > 2.5 * lap_std:
                reasons.append(f"bruit={page['laplacian_var']:.0f}")
            if ela_std > 0 and abs(page["ela"] - ela_median) > 2.5 * ela_std:
                reasons.append(f"ELA={page['ela']:.1f}")
            if abs(page["brightness"] - bright_median) > 30:
                reasons.append(f"luminosité={page['brightness']:.0f}")
            if reasons:
                anomalies.append(LayoutAnomaly(
                    categorie="coherence_multipage_visuelle",
                    severite="warning",
                    description=f"La page {page['page']} diffère des autres ({', '.join(reasons)}).",
                    zone=f"page_{page['page']}",
                    score_impact=5.0,
                ))

    # textual consistency of headers/footers
    page_map = group_elements_by_page(payload.elements)
    if page_map and payload.page_sizes:
        first_header = first_footer = None
        header_scores = []
        footer_scores = []
        for page_id, elements in sorted(page_map.items()):
            _, page_h = payload.page_sizes[page_id] if page_id < len(payload.page_sizes) else (0, 0)
            header_sig = _token_signature(elements, page_h, 0.0, 0.15)
            footer_sig = _token_signature(elements, page_h, 0.85, 1.0)
            if first_header is None:
                first_header = header_sig
                first_footer = footer_sig
            header_similarity = _jaccard(first_header, header_sig) if first_header is not None else 1.0
            footer_similarity = _jaccard(first_footer, footer_sig) if first_footer is not None else 1.0
            header_scores.append(round(header_similarity, 3))
            footer_scores.append(round(footer_similarity, 3))
            if page_id > 0 and header_similarity < 0.20 and header_sig:
                anomalies.append(LayoutAnomaly(
                    categorie="entete_incoherent",
                    severite="warning",
                    description=f"L'en-tête de la page {page_id + 1} diffère fortement de la page 1.",
                    zone=f"page_{page_id + 1}",
                    score_impact=4.0,
                ))
            if page_id > 0 and footer_similarity < 0.20 and footer_sig:
                anomalies.append(LayoutAnomaly(
                    categorie="pied_de_page_incoherent",
                    severite="warning",
                    description=f"Le pied de page de la page {page_id + 1} diffère fortement de la page 1.",
                    zone=f"page_{page_id + 1}",
                    score_impact=4.0,
                ))
        metrics["header_similarity_vs_page1"] = header_scores
        metrics["footer_similarity_vs_page1"] = footer_scores

    # logo shift across pages when images exist
    if payload.images:
        header_graphic_x = []
        for page_id, image in enumerate(payload.images):
            page_elements = page_map.get(page_id, [])
            page_h = payload.page_sizes[page_id][1] if page_id < len(payload.page_sizes) else image.size[1]
            graphic_metrics, _ = detect_graphic_zones(image, page_elements, doc_type, page_h)
            header_graphics = [zone for zone in graphic_metrics.get("graphic_zones", []) if zone["y_norm"] < 0.25]
            if header_graphics:
                header_graphic_x.append(header_graphics[0]["x_norm"])
        if len(header_graphic_x) >= 2:
            std_x = statistics.stdev(header_graphic_x) if len(header_graphic_x) > 2 else max(header_graphic_x) - min(header_graphic_x)
            metrics["header_graphic_x_positions"] = [round(value, 3) for value in header_graphic_x]
            metrics["header_graphic_x_spread"] = round(std_x, 3)
            if std_x > 0.18:
                anomalies.append(LayoutAnomaly(
                    categorie="logo_decale_multipage",
                    severite="warning",
                    description="La position horizontale du logo/en-tête graphique varie fortement entre les pages.",
                    zone="header",
                    score_impact=4.0,
                ))

    return metrics, anomalies
