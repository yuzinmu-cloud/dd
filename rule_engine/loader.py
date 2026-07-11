from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_rule_pack(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    data: dict[str, Any] = {"path": str(root), "metadata": metadata}
    for file in root.glob("*.json"):
        if file.name != "metadata.json":
            data[file.stem] = json.loads(file.read_text(encoding="utf-8"))
    return data
