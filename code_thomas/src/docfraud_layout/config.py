from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class AnalysisConfig:
    document_path: str
    doc_type_override: Optional[str] = None
    enable_visual_layer: bool = True
    enable_candidate_layer: bool = True
    enable_multipage_checks: bool = True
    enable_pdf_font_analysis: bool = True
    render_pdf_pages: bool = True
    alignment_tolerance_px: int = 15
    candidate_window_px: int = 24
    candidate_review_threshold: float = 0.55

    authenticity_bias_points_by_doc_type: Dict[str, float] = field(default_factory=lambda: {
        "ticket_caisse": -2.0,
        "facture": 0.0,
        "releve_bancaire": 2.0,
        "contrat": 1.0,
        "formulaire": 1.0,
        "unknown": 0.0,
    })

    authenticity_bias_points_by_source: Dict[str, float] = field(default_factory=lambda: {
        "native_pdf": 1.0,
        "ocr_scan": -2.0,
        "image": -3.0,
        "json_ocr": 0.0,
        "unknown": 0.0,
    })

    candidate_regexes: Tuple[str, ...] = (
        r"\b\d{1,3}(?:[., ]\d{3})*(?:[.,]\d{2})\b",
        r"\b\d{2}[/-]\d{2}[/-]\d{2,4}\b",
        r"\b[A-Z]{2}\d{2,}[A-Z0-9]*\b",
        r"\b\d{6,}\b",
    )
