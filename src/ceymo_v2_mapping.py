"""Map CeyMo road-marking labels to the GOV-01 V2 label vocabulary."""

from __future__ import annotations


CEYMO_LABEL_NAMES = {
    "BL": "Bus Lane",
    "CL": "Cycle Lane",
    "DM": "Diamond",
    "JB": "Junction Box",
    "LA": "Left Arrow",
    "PC": "Pedestrian Crossing",
    "RA": "Right Arrow",
    "SA": "Straight Arrow",
    "SL": "Slow",
    "SLA": "Straight-Left Arrow",
    "SRA": "Straight-Right Arrow",
}


def map_ceymo_label(source_label: str) -> str:
    """Return the general V2 object label for a known CeyMo marking."""
    if source_label not in CEYMO_LABEL_NAMES:
        raise ValueError(f"Unsupported CeyMo label: {source_label}")
    return "road_marking"


def road_marking_present(source_labels: list[str]) -> bool:
    """Return whether a verified CeyMo annotation contains a road marking."""
    for source_label in source_labels:
        map_ceymo_label(source_label)
    return bool(source_labels)
