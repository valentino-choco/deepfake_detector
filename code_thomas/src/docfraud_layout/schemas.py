from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BBoxElement:
    text: str
    confidence: float
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    page_id: int = 0
    font_name: Optional[str] = None
    source: str = "ocr"

    @property
    def width(self) -> int:
        return max(0, self.x_max - self.x_min)

    @property
    def height(self) -> int:
        return max(0, self.y_max - self.y_min)

    @property
    def center_x(self) -> float:
        return (self.x_min + self.x_max) / 2.0

    @property
    def center_y(self) -> float:
        return (self.y_min + self.y_max) / 2.0

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return (self.x_min, self.y_min, self.x_max, self.y_max)


@dataclass
class DocumentPayload:
    source_kind: str
    page_count: int
    elements: List[BBoxElement]
    page_sizes: List[Tuple[int, int]] = field(default_factory=list)
    images: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutAnomaly:
    categorie: str
    severite: str
    description: str
    zone: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    score_impact: float = 0.0


@dataclass
class CandidateRegion:
    candidate_id: str
    text: str
    page_id: int
    bbox: Tuple[int, int, int, int]
    candidate_type: str
    local_context: List[str] = field(default_factory=list)


@dataclass
class CandidateScore:
    candidate_id: str
    text: str
    candidate_type: str
    page_id: int
    raw_score: float
    calibrated_score: float
    signals: Dict[str, float]
    verdict: str
    bbox: Tuple[int, int, int, int]


@dataclass
class AnalysisReport:
    type_document: str
    source_kind: str
    nb_pages: int
    nb_elements_ocr: int
    score_layout_raw: float
    score_layout: float
    sections_detectees: Dict[str, Any] = field(default_factory=dict)
    sections_manquantes: List[str] = field(default_factory=list)
    metriques_structurelles: Dict[str, Any] = field(default_factory=dict)
    metriques_visuelles: Dict[str, Any] = field(default_factory=dict)
    metriques_polices: Dict[str, Any] = field(default_factory=dict)
    metriques_multipage: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[LayoutAnomaly] = field(default_factory=list)
    candidates: List[CandidateScore] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type_document": self.type_document,
            "source_kind": self.source_kind,
            "nb_pages": self.nb_pages,
            "nb_elements_ocr": self.nb_elements_ocr,
            "score_layout_raw": self.score_layout_raw,
            "score_layout": self.score_layout,
            "sections_detectees": self.sections_detectees,
            "sections_manquantes": self.sections_manquantes,
            "metriques_structurelles": self.metriques_structurelles,
            "metriques_visuelles": self.metriques_visuelles,
            "metriques_polices": self.metriques_polices,
            "metriques_multipage": self.metriques_multipage,
            "anomalies": [asdict(a) for a in self.anomalies],
            "candidates": [asdict(c) for c in self.candidates],
            "metadata": self.metadata,
        }


@dataclass
class DatasetSpec:
    slug: str
    name: str
    task_focus: str
    public_status: str
    recommended_use: str
    notes: str
