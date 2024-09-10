from __future__ import annotations

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def save_fixture(name: str, data: dict):
    """Save API response data to a fixture file."""
    file_path = FIXTURE_DIR / f"{name}.json"
    with open(file_path, "w") as f:
        json.dump(data, f)

def load_fixture(name: str) -> dict:
    """Load API response data from a fixture file."""
    file_path = FIXTURE_DIR / f"{name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Fixture {name} not found")
    with open(file_path) as f:
        return json.load(f)
