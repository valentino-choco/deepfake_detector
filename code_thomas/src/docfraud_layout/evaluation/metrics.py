from __future__ import annotations

from typing import Iterable

import numpy as np


def classification_metrics(y_true: Iterable[int], y_score: Iterable[float], threshold: float = 0.5) -> dict:
    y_true = np.asarray(list(y_true)).astype(int)
    y_score = np.asarray(list(y_score)).astype(float)
    y_pred = (y_score >= threshold).astype(int)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())

    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    accuracy = (tp + tn) / max(1, len(y_true))

    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "accuracy": round(float(accuracy), 4),
    }


def pixel_metrics(pred_mask: np.ndarray, true_mask: np.ndarray, threshold: float = 0.5) -> dict:
    pred = (pred_mask >= threshold).astype(np.uint8)
    true = (true_mask > 0).astype(np.uint8)

    intersection = int((pred & true).sum())
    union = int(((pred | true) > 0).sum())
    pred_sum = int(pred.sum())
    true_sum = int(true.sum())

    iou = intersection / max(1, union)
    precision = intersection / max(1, pred_sum)
    recall = intersection / max(1, true_sum)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)

    return {
        "iou": round(float(iou), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "pred_pixels": pred_sum,
        "true_pixels": true_sum,
    }
