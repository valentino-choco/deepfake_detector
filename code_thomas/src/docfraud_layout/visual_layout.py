from __future__ import annotations

import io
import statistics
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

from .reference_data import REFERENCE_LAYOUTS
from .schemas import BBoxElement, LayoutAnomaly


def pil_to_bgr(image) -> np.ndarray:
    if isinstance(image, np.ndarray):
        if image.ndim == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if image.dtype == np.uint8 else image
        return image
    return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def compute_ela(image_bgr: np.ndarray, quality: int = 90) -> float:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer)
    recompressed_bgr = cv2.cvtColor(np.array(recompressed.convert("RGB")), cv2.COLOR_RGB2BGR)
    diff = cv2.absdiff(image_bgr, recompressed_bgr)
    return float(np.mean(diff))


def analyze_header_footer_consistency(image, doc_type: str) -> Tuple[Dict, List[LayoutAnomaly]]:
    image_bgr = pil_to_bgr(image)
    anomalies: List[LayoutAnomaly] = []
    height, width = image_bgr.shape[:2]

    header_pct = 0.15 if doc_type != "ticket_caisse" else 0.25
    footer_pct = 0.85 if doc_type != "ticket_caisse" else 0.75
    bands = {
        "header": image_bgr[0:int(height * header_pct), :],
        "body": image_bgr[int(height * header_pct):int(height * footer_pct), :],
        "footer": image_bgr[int(height * footer_pct):, :],
    }

    metrics: Dict[str, Dict] = {}
    for name, band in bands.items():
        if band.size == 0:
            continue
        gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        ela = compute_ela(band)
        metrics[name] = {"laplacian_var": round(lap_var, 2), "ela": round(ela, 2)}

    if "body" in metrics and metrics["body"]["laplacian_var"] > 0:
        body_lap = metrics["body"]["laplacian_var"]
        body_ela = metrics["body"]["ela"]
        for zone in ["header", "footer"]:
            if zone not in metrics:
                continue
            zone_lap = metrics[zone]["laplacian_var"]
            zone_ela = metrics[zone]["ela"]
            lap_ratio = zone_lap / body_lap if body_lap else 0
            metrics[f"{zone}_body_lap_ratio"] = round(lap_ratio, 3)
            lap_threshold = 3.0 if doc_type == "ticket_caisse" else 2.5
            ela_threshold = 8.0 if doc_type == "ticket_caisse" else 5.0

            if lap_ratio > lap_threshold or (lap_ratio > 0 and 1.0 / lap_ratio > lap_threshold):
                anomalies.append(LayoutAnomaly(
                    categorie="coherence_visuelle_header_footer",
                    severite="warning",
                    description=f"Le bruit du {zone} diffère fortement du corps (ratio Laplacien={lap_ratio:.2f}).",
                    zone=zone,
                    score_impact=5.0,
                ))

            ela_diff = abs(zone_ela - body_ela)
            if ela_diff > ela_threshold:
                anomalies.append(LayoutAnomaly(
                    categorie="compression_header_footer",
                    severite="warning",
                    description=f"Le {zone} présente une ELA différente du corps (Δ={ela_diff:.1f}).",
                    zone=zone,
                    score_impact=5.0,
                ))
    return metrics, anomalies


def detect_graphic_zones(image, elements: List[BBoxElement], doc_type: str, page_h: int) -> Tuple[Dict, List[LayoutAnomaly]]:
    image_bgr = pil_to_bgr(image)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(gx ** 2 + gy ** 2)

    grid_rows, grid_cols = 5, 3
    cell_h, cell_w = height // grid_rows, width // grid_cols
    text_density = np.zeros((grid_rows, grid_cols))
    for element in elements:
        row = min(int(element.center_y / max(1, cell_h)), grid_rows - 1)
        col = min(int(element.center_x / max(1, cell_w)), grid_cols - 1)
        text_density[row, col] += 1

    graphic_zones = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            cell_grad = grad_mag[row * cell_h:(row + 1) * cell_h, col * cell_w:(col + 1) * cell_w]
            mean_grad = float(np.mean(cell_grad)) if cell_grad.size else 0.0
            if mean_grad > 15.0 and text_density[row, col] < 3:
                cell_gray = gray[row * cell_h:(row + 1) * cell_h, col * cell_w:(col + 1) * cell_w]
                sharpness = float(cv2.Laplacian(cell_gray, cv2.CV_64F).var()) if cell_gray.size else 0.0
                zone = {
                    "row": row,
                    "col": col,
                    "x_norm": round((col + 0.5) / grid_cols, 3),
                    "y_norm": round((row + 0.5) / grid_rows, 3),
                    "gradient_mean": round(mean_grad, 2),
                    "sharpness": round(sharpness, 2),
                    "text_elements": int(text_density[row, col]),
                }
                graphic_zones.append(zone)

    anomalies: List[LayoutAnomaly] = []
    metrics = {"graphic_zones": graphic_zones, "nb_detected": len(graphic_zones)}
    ref = REFERENCE_LAYOUTS.get(doc_type)
    expected_zone = ref.get("logo_zone") if ref else None

    header_graphics = [zone for zone in graphic_zones if zone["y_norm"] < 0.25]
    if expected_zone:
        if not header_graphics:
            anomalies.append(LayoutAnomaly(
                categorie="logo_absent",
                severite="info",
                description="Aucune zone graphique de type logo n'a été détectée dans l'en-tête.",
                zone="header",
                score_impact=3.0,
            ))
        else:
            x_lo, x_hi = expected_zone["x"]
            y_lo, y_hi = expected_zone["y"]
            in_expected = [
                zone for zone in header_graphics
                if x_lo <= zone["x_norm"] <= x_hi and y_lo <= zone["y_norm"] <= y_hi
            ]
            if not in_expected:
                anomalies.append(LayoutAnomaly(
                    categorie="logo_decale",
                    severite="warning",
                    description=(
                        f"Une zone graphique est détectée dans l'en-tête mais hors de la zone attendue "
                        f"x=[{x_lo:.2f},{x_hi:.2f}], y=[{y_lo:.2f},{y_hi:.2f}]."
                    ),
                    zone="header",
                    score_impact=4.0,
                ))

    for zone in header_graphics:
        if zone["sharpness"] < 50.0:
            anomalies.append(LayoutAnomaly(
                categorie="logo_flou",
                severite="warning",
                description=f"Zone graphique d'en-tête floue (netteté={zone['sharpness']:.1f}).",
                zone=f"row={zone['row']},col={zone['col']}",
                score_impact=4.0,
            ))
    return metrics, anomalies


def analyze_local_ink_density(image) -> Tuple[Dict, List[LayoutAnomaly]]:
    image_bgr = pil_to_bgr(image)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    grid_rows, grid_cols = 8, 6
    height, width = gray.shape[:2]
    cell_h, cell_w = height // grid_rows, width // grid_cols
    ratios = np.zeros((grid_rows, grid_cols))
    for row in range(grid_rows):
        for col in range(grid_cols):
            cell = binary[row * cell_h:(row + 1) * cell_h, col * cell_w:(col + 1) * cell_w]
            ratios[row, col] = float(np.mean(cell)) / 255.0 if cell.size else 0.0

    text_cells = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            if ratios[row, col] > 0.01:
                text_cells.append({"r": row, "c": col, "ink_ratio": round(float(ratios[row, col]), 4)})

    if len(text_cells) < 4:
        return {"note": "Pas assez de cellules textuelles"}, []

    values = [cell["ink_ratio"] for cell in text_cells]
    median_ratio = statistics.median(values)
    std_ratio = statistics.stdev(values) if len(values) > 2 else 0.0

    outlier_cells = []
    if std_ratio > 0:
        for cell in text_cells:
            z_score = abs(cell["ink_ratio"] - median_ratio) / std_ratio
            if z_score > 3.0:
                cell["z_score"] = round(z_score, 2)
                outlier_cells.append(cell)

    anomalies: List[LayoutAnomaly] = []
    body_outliers = [cell for cell in outlier_cells if cell["r"] > 0]
    if body_outliers:
        anomalies.append(LayoutAnomaly(
            categorie="densite_encre_locale",
            severite="info",
            description=f"{len(body_outliers)} cellules ont une densité d'encre aberrante dans le corps du document.",
            score_impact=3.0,
        ))

    return {
        "nb_text_cells": len(text_cells),
        "ink_ratio_median": round(median_ratio, 4),
        "ink_ratio_std": round(std_ratio, 4),
        "nb_outlier_cells": len(outlier_cells),
    }, anomalies
