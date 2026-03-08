from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .schemas import BBoxElement


def cluster_values(values: List[int], tolerance: int = 15, min_cluster_size: int = 2) -> List[int]:
    if not values:
        return []
    values = sorted(values)
    clusters: List[List[int]] = [[values[0]]]
    for value in values[1:]:
        if value - clusters[-1][-1] <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    result = []
    for cluster in clusters:
        if len(cluster) >= min_cluster_size:
            result.append(int(round(sum(cluster) / len(cluster))))
    return result


def group_elements_by_page(elements: Iterable[BBoxElement]) -> Dict[int, List[BBoxElement]]:
    pages: Dict[int, List[BBoxElement]] = defaultdict(list)
    for element in elements:
        pages[element.page_id].append(element)
    return dict(pages)
