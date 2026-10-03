"""Small, testable display decisions for the GOV-01 Streamlit app."""

from __future__ import annotations

from collections.abc import Sequence


def select_result_view(detected_conditions: Sequence[str]) -> str:
    """Choose the one result view that matches E7's locked detections.

    Phase 2's locked thresholds decide whether the image is treated as a
    multiple-condition result. Zero or one E7 detection uses the Phase 1
    single-class view; two or more detections use the Phase 2 view.
    """
    return "multiple_conditions" if len(detected_conditions) >= 2 else "one_condition"
