from __future__ import annotations

from typing import List

from .candidate_signals import aggregate_candidate_signals, compute_candidate_signals
from .calibration import calibrate_candidate_score, verdict_from_candidate_score
from .candidates import extract_numeric_candidates, infer_document_type
from .config import AnalysisConfig
from .font_analysis import (
    analyze_element_font_usage,
    analyze_font_consistency_per_zone,
    analyze_font_sizes_global,
    analyze_pdf_fonts,
)
from .geometry import group_elements_by_page
from .io import load_document
from .layout_alignment import analyze_alignment_consistency, analyze_spacing_consistency
from .layout_reference import analyze_field_positions, analyze_reference_sections
from .multipage import analyze_multipage_consistency
from .scoring import compute_layout_scores
from .schemas import AnalysisReport, CandidateScore, LayoutAnomaly
from .visual_layout import analyze_header_footer_consistency, analyze_local_ink_density, detect_graphic_zones


def _page_size_for_first_page(payload) -> tuple[int, int]:
    if payload.page_sizes:
        return payload.page_sizes[0]
    if payload.elements:
        width = max(element.x_max for element in payload.elements) + 50
        height = max(element.y_max for element in payload.elements) + 50
        return width, height
    if payload.images:
        return payload.images[0].size
    return 0, 0


def analyze_document(config: AnalysisConfig) -> AnalysisReport:
    payload = load_document(config.document_path, config)
    doc_type = config.doc_type_override or infer_document_type(payload.elements)
    page_w, page_h = _page_size_for_first_page(payload)

    anomalies: List[LayoutAnomaly] = []
    structural_metrics = {}
    visual_metrics = {}
    font_metrics = {}
    multipage_metrics = {}
    sections_detectees = {}
    sections_manquantes: List[str] = []

    if payload.elements:
        section_metrics, sections_manquantes, section_anomalies = analyze_reference_sections(
            payload.elements, doc_type, page_h
        )
        field_metrics, field_anomalies = analyze_field_positions(payload.elements, doc_type, page_h)
        alignment_metrics, alignment_anomalies = analyze_alignment_consistency(
            payload.elements, page_w, page_h, doc_type, tolerance_px=config.alignment_tolerance_px
        )
        spacing_metrics, spacing_anomalies = analyze_spacing_consistency(payload.elements)
        global_font_metrics, global_font_anomalies = analyze_font_sizes_global(payload.elements)
        zone_font_metrics, zone_font_anomalies = analyze_font_consistency_per_zone(payload.elements, doc_type, page_h)
        usage_font_metrics, usage_font_anomalies = analyze_element_font_usage(payload.elements)

        structural_metrics = {
            "reference_sections": section_metrics,
            "field_positions": field_metrics,
            "alignment": alignment_metrics,
            "spacing": spacing_metrics,
        }
        font_metrics = {
            "global_heights": global_font_metrics,
            "zone_consistency": zone_font_metrics,
            "element_font_usage": usage_font_metrics,
        }
        sections_detectees = section_metrics.get("sections", {})
        anomalies.extend(section_anomalies + field_anomalies + alignment_anomalies + spacing_anomalies)
        anomalies.extend(global_font_anomalies + zone_font_anomalies + usage_font_anomalies)

    if config.enable_visual_layer and payload.images:
        first_image = payload.images[0]
        first_page_elements = group_elements_by_page(payload.elements).get(0, [])
        header_footer_metrics, header_footer_anomalies = analyze_header_footer_consistency(first_image, doc_type)
        graphic_metrics, graphic_anomalies = detect_graphic_zones(first_image, first_page_elements, doc_type, page_h)
        ink_metrics, ink_anomalies = analyze_local_ink_density(first_image)
        visual_metrics = {
            "header_footer": header_footer_metrics,
            "graphic_zones": graphic_metrics,
            "ink_density": ink_metrics,
        }
        anomalies.extend(header_footer_anomalies + graphic_anomalies + ink_anomalies)

    if config.enable_multipage_checks:
        multipage_metrics, multipage_anomalies = analyze_multipage_consistency(payload, doc_type)
        anomalies.extend(multipage_anomalies)

    if config.enable_pdf_font_analysis and config.document_path.lower().endswith(".pdf"):
        pdf_font_metrics, pdf_font_anomalies = analyze_pdf_fonts(config.document_path)
        font_metrics["pdf_fonts"] = pdf_font_metrics
        anomalies.extend(pdf_font_anomalies)

    candidate_scores: List[CandidateScore] = []
    if config.enable_candidate_layer and payload.elements:
        candidates = extract_numeric_candidates(payload.elements, config)
        for candidate in candidates:
            signals = compute_candidate_signals(candidate, payload.elements)
            raw_score = aggregate_candidate_signals(signals)
            calibrated = calibrate_candidate_score(raw_score, doc_type, payload.source_kind)
            verdict = verdict_from_candidate_score(calibrated, config.candidate_review_threshold)
            candidate_scores.append(CandidateScore(
                candidate_id=candidate.candidate_id,
                text=candidate.text,
                candidate_type=candidate.candidate_type,
                page_id=candidate.page_id,
                raw_score=raw_score,
                calibrated_score=calibrated,
                signals=signals,
                verdict=verdict,
                bbox=candidate.bbox,
            ))
        risky = [candidate for candidate in candidate_scores if candidate.verdict in {"review", "high_risk"}]
        if risky:
            anomalies.append(LayoutAnomaly(
                categorie="candidats_numeriques_suspects",
                severite="warning" if len(risky) < 3 else "critical",
                description=f"{len(risky)} candidat(s) numériques demandent une revue humaine ciblée.",
                score_impact=min(12.0, 2.5 * len(risky)),
            ))

    if payload.source_kind == "image":
        anomalies.append(LayoutAnomaly(
            categorie="source_image",
            severite="info",
            description="Document chargé comme image seule : l'analyse de structure et de police est moins riche qu'un PDF natif.",
            score_impact=2.0,
        ))

    score_raw, score_cal = compute_layout_scores(anomalies, candidate_scores, doc_type, payload.source_kind, config)

    return AnalysisReport(
        type_document=doc_type,
        source_kind=payload.source_kind,
        nb_pages=payload.page_count,
        nb_elements_ocr=len(payload.elements),
        score_layout_raw=score_raw,
        score_layout=score_cal,
        sections_detectees=sections_detectees,
        sections_manquantes=sections_manquantes,
        metriques_structurelles=structural_metrics,
        metriques_visuelles=visual_metrics,
        metriques_polices=font_metrics,
        metriques_multipage=multipage_metrics,
        anomalies=sorted(anomalies, key=lambda anomaly: anomaly.score_impact, reverse=True),
        candidates=sorted(candidate_scores, key=lambda candidate: candidate.calibrated_score, reverse=True),
        metadata=payload.metadata,
    )
