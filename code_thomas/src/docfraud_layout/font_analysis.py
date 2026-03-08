from __future__ import annotations

import statistics
from collections import Counter
from typing import Dict, List, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer

from .io import normalize_font_name
from .reference_data import REFERENCE_LAYOUTS
from .schemas import BBoxElement, LayoutAnomaly


def analyze_font_sizes_global(elements: List[BBoxElement]) -> Tuple[Dict, List[LayoutAnomaly]]:
    heights = [element.height for element in elements if len(element.text.strip()) > 2 and element.height > 0]
    if len(heights) < 5:
        return {}, []
    anomalies: List[LayoutAnomaly] = []
    median_height = statistics.median(heights)
    std_height = statistics.stdev(heights) if len(heights) > 2 else 0.0
    unique_heights = sorted(set(int(round(value)) for value in heights))
    if len(unique_heights) > 5:
        anomalies.append(LayoutAnomaly(
            categorie="tailles_police_multiples",
            severite="warning",
            description=f"{len(unique_heights)} tailles de police proxifiées détectées ; attendu 2 à 4 sur un document standard.",
            score_impact=4.0,
        ))
    return {
        "median_height_px": round(median_height, 2),
        "std_height_px": round(std_height, 2),
        "nb_height_clusters": len(unique_heights),
        "height_clusters": unique_heights[:10],
    }, anomalies


def analyze_font_consistency_per_zone(elements: List[BBoxElement], doc_type: str, page_h: int) -> Tuple[Dict, List[LayoutAnomaly]]:
    anomalies: List[LayoutAnomaly] = []
    ref = REFERENCE_LAYOUTS.get(doc_type)
    if not ref or page_h <= 0:
        return {}, []

    zone_heights = {}
    for section_def in ref["sections_attendues"]:
        name = section_def["nom"]
        y_lo = section_def["zone_y"][0] * page_h
        y_hi = section_def["zone_y"][1] * page_h
        heights = [
            element.height for element in elements
            if y_lo <= element.center_y <= y_hi and len(element.text.strip()) > 2 and element.height > 0
        ]
        if len(heights) >= 3:
            zone_heights[name] = heights

    if len(zone_heights) < 2:
        return {}, []

    zone_stats = {}
    for name, heights in zone_heights.items():
        median_height = statistics.median(heights)
        std_height = statistics.stdev(heights) if len(heights) > 2 else 0.0
        cv = std_height / median_height if median_height > 0 else 0.0
        zone_stats[name] = {
            "median_h": round(median_height, 1),
            "std_h": round(std_height, 1),
            "cv": round(cv, 3),
            "n_elements": len(heights),
        }

    all_cvs = [stats["cv"] for stats in zone_stats.values()]
    global_cv_median = statistics.median(all_cvs) if all_cvs else 0.0
    for name, stats in zone_stats.items():
        if stats["cv"] > 0.5 or (global_cv_median > 0 and stats["cv"] > 2.5 * global_cv_median):
            anomalies.append(LayoutAnomaly(
                categorie="police_zone",
                severite="warning",
                description=(
                    f"La section '{name}' présente des hauteurs de texte très hétérogènes "
                    f"(CV={stats['cv']:.2f}, médiane={stats['median_h']:.0f}px)."
                ),
                zone=name,
                score_impact=4.0,
            ))

    medians = [stats["median_h"] for stats in zone_stats.values()]
    global_median = statistics.median(medians) if medians else 0.0
    global_std = statistics.stdev(medians) if len(medians) > 2 else 0.0
    for name, stats in zone_stats.items():
        if global_std > 0:
            z_score = abs(stats["median_h"] - global_median) / global_std
            if z_score > 2.5:
                anomalies.append(LayoutAnomaly(
                    categorie="police_zone_mediane",
                    severite="info",
                    description=(
                        f"La taille médiane de la section '{name}' ({stats['median_h']:.0f}px) "
                        f"dévie du reste du document (z={z_score:.1f})."
                    ),
                    zone=name,
                    score_impact=2.0,
                ))
    return zone_stats, anomalies


def analyze_element_font_usage(elements: List[BBoxElement]) -> Tuple[Dict, List[LayoutAnomaly]]:
    anomalies: List[LayoutAnomaly] = []
    fonts = [normalize_font_name(element.font_name) for element in elements if element.font_name]
    fonts = [font for font in fonts if font]
    if not fonts:
        return {}, []

    counts = Counter(fonts)
    total = sum(counts.values())
    metrics = {
        "nb_font_families_elements": len(counts),
        "font_usage": dict(counts.most_common(10)),
    }
    if len(counts) > 4:
        anomalies.append(LayoutAnomaly(
            categorie="polices_non_standard",
            severite="warning",
            description=f"{len(counts)} familles de polices détectées au niveau OCR/PDF ; attendu 1 à 3 dans la plupart des documents métier.",
            score_impact=5.0,
        ))
    for font_name, count in counts.items():
        ratio = count / max(1, total)
        if ratio < 0.08 and count >= 1:
            anomalies.append(LayoutAnomaly(
                categorie="police_rare",
                severite="info",
                description=f"La police '{font_name}' est rare dans le document ({ratio:.1%} des éléments) ; possible insertion locale.",
                zone=font_name,
                score_impact=1.5,
            ))
        if any(keyword in font_name for keyword in ["courier", "symbol", "dingbats"]):
            anomalies.append(LayoutAnomaly(
                categorie="police_non_standard",
                severite="warning",
                description=f"Police inhabituelle détectée : '{font_name}'.",
                zone=font_name,
                score_impact=3.0,
            ))
    return metrics, anomalies


def _base_family(font_name: str) -> str:
    normalized = normalize_font_name(font_name) or font_name.lower()
    for suffix in ["bold", "italic", "regular", "light", "medium", "semibold", "mt"]:
        normalized = normalized.replace(suffix, "")
    return normalized.strip("-_, ") or font_name.lower()


def analyze_pdf_fonts(pdf_path: str) -> Tuple[Dict, List[LayoutAnomaly]]:
    anomalies: List[LayoutAnomaly] = []
    font_usage = Counter()
    font_by_page = {}
    char_count = 0

    try:
        for page_number, page_layout in enumerate(extract_pages(pdf_path)):
            page_fonts = set()
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                font_name = normalize_font_name(character.fontname) or character.fontname.lower()
                                char_count += 1
                                font_usage[font_name] += 1
                                page_fonts.add(font_name)
            font_by_page[page_number] = page_fonts
    except Exception as exc:
        return {"error": str(exc)}, []

    if char_count == 0:
        return {"note": "Pas de texte natif exploitable"}, []

    families = Counter()
    for font_name, count in font_usage.items():
        families[_base_family(font_name)] += count

    metrics = {
        "nb_characters": char_count,
        "nb_font_families_pdf": len(families),
        "families": dict(families.most_common(10)),
        "raw_fonts": dict(font_usage.most_common(15)),
    }

    if len(families) > 5:
        anomalies.append(LayoutAnomaly(
            categorie="police_famille_pdf",
            severite="warning",
            description=(
                f"{len(families)} familles de polices PDF détectées "
                f"({', '.join(name for name, _ in families.most_common(5))})."
            ),
            score_impact=5.0,
        ))

    for family_name, count in families.items():
        ratio = count / max(1, char_count)
        if ratio < 0.01 and count > 5:
            anomalies.append(LayoutAnomaly(
                categorie="police_rare_pdf",
                severite="info",
                description=f"La famille '{family_name}' ne représente que {ratio:.1%} des caractères PDF.",
                zone=family_name,
                score_impact=1.5,
            ))

    if len(font_by_page) > 1 and font_by_page:
        global_fonts = set.intersection(*font_by_page.values()) if all(font_by_page.values()) else set()
        all_fonts = set.union(*font_by_page.values()) if any(font_by_page.values()) else set()
        isolated_fonts = all_fonts - global_fonts
        for font_name in isolated_fonts:
            pages = [page + 1 for page, fonts in font_by_page.items() if font_name in fonts]
            anomalies.append(LayoutAnomaly(
                categorie="police_page_isolee",
                severite="info",
                description=f"La police '{font_name}' n'apparaît que sur la/les page(s) {pages}.",
                zone=font_name,
                score_impact=1.0,
            ))
    return metrics, anomalies
