from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable, List

from .config import AnalysisConfig
from .reference_data import REFERENCE_LAYOUTS
from .schemas import BBoxElement, CandidateRegion


def infer_document_type(elements: Iterable[BBoxElement]) -> str:
    text = " ".join(e.text.lower() for e in elements if e.text).strip()
    if not text:
        return "unknown"
    if any(k in text for k in ["facture", "invoice", "échéance"]):
        return "facture"
    if any(k in text for k in ["ticket", "merci", "caisse"]) and "facture" not in text:
        return "ticket_caisse"
    if any(k in text for k in ["iban", "solde", "relevé", "crédit", "débit"]):
        return "releve_bancaire"
    if any(k in text for k in ["contrat", "convention", "article", "lu et approuvé"]):
        return "contrat"
    # fallback: best keyword overlap with reference layouts
    best_doc, best_score = "unknown", 0
    for doc_type, spec in REFERENCE_LAYOUTS.items():
        keywords = set()
        for values in spec["keywords_sections"].values():
            keywords.update(v.lower() for v in values)
        score = sum(keyword in text for keyword in keywords)
        if score > best_score:
            best_doc, best_score = doc_type, score
    return best_doc if best_score > 0 else "unknown"


def _candidate_type_from_text(text: str) -> str:
    normalized = text.strip()
    if re.fullmatch(r"\d{2}[/-]\d{2}[/-]\d{2,4}", normalized):
        return "date"
    if re.search(r"[.,]\d{2}$", normalized):
        return "amount"
    if re.fullmatch(r"\d{6,}", normalized.replace(" ", "")):
        return "long_numeric"
    return "alphanumeric_ref"


def extract_numeric_candidates(elements: List[BBoxElement], config: AnalysisConfig) -> List[CandidateRegion]:
    regexes = [re.compile(pattern) for pattern in config.candidate_regexes]
    per_page = defaultdict(list)
    for element in elements:
        per_page[element.page_id].append(element)

    candidates: List[CandidateRegion] = []
    counter = 0
    for page_id, page_elements in per_page.items():
        page_elements_sorted = sorted(page_elements, key=lambda e: (e.y_min, e.x_min))
        for index, element in enumerate(page_elements_sorted):
            text = element.text.strip()
            if not text:
                continue
            if not any(regex.search(text) for regex in regexes):
                continue
            context_slice = page_elements_sorted[max(0, index - 2): index + 3]
            local_context = [ctx.text for ctx in context_slice if ctx.text != text]
            counter += 1
            candidates.append(CandidateRegion(
                candidate_id=f"cand_{counter:04d}",
                text=text,
                page_id=page_id,
                bbox=element.bbox,
                candidate_type=_candidate_type_from_text(text),
                local_context=local_context,
            ))
    return candidates
