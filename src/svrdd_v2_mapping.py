"""Exact SVRDD-to-V2 condition mapping used before any data conversion.

The mapping is intentionally limited to the four V2 conditions available from
SVRDD. It does not invent look-alike labels such as shadow or puddle, because
SVRDD does not provide them.
"""
from __future__ import annotations

from collections.abc import Iterable


SVRDD_TO_V2 = {
    "longitudinal crack": "crack",
    "transverse crack": "crack",
    "alligator crack": "crack",
    "pothole": "pothole",
    "manhole cover": "manhole_cover",
    "longitudinal patch": "repaired_road",
    "transverse patch": "repaired_road",
}

# Used only when an SVRDD image needs one source-derived multi-class label.
# It is not the complete V2 priority order for future look-alike sources.
SVRDD_MULTICLASS_PRIORITY = (
    "pothole",
    "crack",
    "repaired_road",
    "manhole_cover",
)


def map_source_label(source_label: str) -> str:
    """Convert one SVRDD label, or stop instead of silently guessing."""
    try:
        return SVRDD_TO_V2[source_label]
    except KeyError as error:
        raise ValueError(f"Unsupported SVRDD source label: {source_label!r}") from error


def source_categories_to_multilabels(source_labels: Iterable[str]) -> dict[str, bool]:
    """Create the four V2 Yes/No labels supported by SVRDD."""
    mapped = {map_source_label(label) for label in source_labels}
    return {
        "pothole_present": "pothole" in mapped,
        "crack_present": "crack" in mapped,
        "manhole_cover_present": "manhole_cover" in mapped,
        "repaired_road_present": "repaired_road" in mapped,
    }


def source_categories_to_multiclass(source_labels: Iterable[str]) -> str:
    """Return one V2 condition using the documented SVRDD-only priority rule."""
    mapped = {map_source_label(label) for label in source_labels}
    for condition in SVRDD_MULTICLASS_PRIORITY:
        if condition in mapped:
            return condition
    raise ValueError("An SVRDD record needs at least one supported source label")
