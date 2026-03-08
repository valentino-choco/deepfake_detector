from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .config import AnalysisConfig
from .schemas import BBoxElement, DocumentPayload

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None

try:
    from PIL import Image
except Exception:
    Image = None


def normalize_font_name(font_name: str | None) -> str | None:
    if not font_name:
        return None
    cleaned = font_name.split("+")[-1]
    cleaned = cleaned.split("-")[0]
    cleaned = cleaned.replace("_", "").replace(" ", "")
    return cleaned.strip().lower() or None


def _load_json_ocr(path: Path) -> DocumentPayload:
    data = json.loads(path.read_text(encoding="utf-8"))
    elements: List[BBoxElement] = []
    page_sizes = []
    page_count = 0
    for page_idx, page in enumerate(data.get("pages", [])):
        page_count += 1
        width = int(page.get("width", 0))
        height = int(page.get("height", 0))
        page_sizes.append((width, height))
        for item in page.get("elements", []):
            elements.append(BBoxElement(
                text=str(item.get("text", "")),
                confidence=float(item.get("confidence", 0.0)),
                x_min=int(item.get("x_min", 0)),
                y_min=int(item.get("y_min", 0)),
                x_max=int(item.get("x_max", 0)),
                y_max=int(item.get("y_max", 0)),
                page_id=page_idx,
                font_name=normalize_font_name(item.get("font_name")),
                source="json_ocr",
            ))
    return DocumentPayload(
        source_kind="json_ocr",
        page_count=max(1, page_count),
        elements=elements,
        page_sizes=page_sizes,
        metadata={"path": str(path)},
    )


def _render_pdf_pages(path: Path):
    if convert_from_path is None:
        return []
    try:
        return convert_from_path(str(path), dpi=150)
    except Exception:
        return []


def _load_native_pdf(path: Path, config: AnalysisConfig) -> DocumentPayload:
    if pdfplumber is None:
        raise RuntimeError("pdfplumber n'est pas disponible")

    elements: List[BBoxElement] = []
    page_sizes = []
    metadata = {"path": str(path)}
    with pdfplumber.open(str(path)) as pdf:
        metadata.update({k: str(v) for k, v in (pdf.metadata or {}).items() if v is not None})
        for page_idx, page in enumerate(pdf.pages):
            page_sizes.append((int(page.width), int(page.height)))
            words = page.extract_words(extra_attrs=["fontname"]) or []
            for word in words:
                elements.append(BBoxElement(
                    text=str(word.get("text", "")),
                    confidence=1.0,
                    x_min=int(word.get("x0", 0)),
                    y_min=int(word.get("top", 0)),
                    x_max=int(word.get("x1", 0)),
                    y_max=int(word.get("bottom", 0)),
                    page_id=page_idx,
                    font_name=normalize_font_name(word.get("fontname")),
                    source="native_pdf",
                ))
    images = _render_pdf_pages(path) if config.render_pdf_pages else []
    source_kind = "native_pdf" if elements else "ocr_scan"
    return DocumentPayload(
        source_kind=source_kind,
        page_count=max(1, len(page_sizes)),
        elements=elements,
        page_sizes=page_sizes,
        images=images,
        metadata=metadata,
    )


def _load_image(path: Path) -> DocumentPayload:
    if Image is None:
        raise RuntimeError("Pillow n'est pas disponible")
    image = Image.open(path).convert("RGB")
    return DocumentPayload(
        source_kind="image",
        page_count=1,
        elements=[],
        images=[image],
        page_sizes=[image.size],
        metadata={"path": str(path)},
    )


def load_document(document_path: str, config: AnalysisConfig | None = None) -> DocumentPayload:
    path = Path(document_path)
    if not path.exists():
        raise FileNotFoundError(f"Document introuvable : {path}")
    config = config or AnalysisConfig(document_path=str(path))

    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json_ocr(path)
    if suffix == ".pdf":
        return _load_native_pdf(path, config)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
        return _load_image(path)
    raise ValueError(f"Extension non supportée : {suffix}")
