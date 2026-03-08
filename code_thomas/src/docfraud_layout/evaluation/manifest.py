from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def load_manifest(path: str | Path) -> List[Dict]:
    path = Path(path)
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
