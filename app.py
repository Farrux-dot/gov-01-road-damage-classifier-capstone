"""One-upload Streamlit interface for GOV-01 Phases 1 and 2."""

from pathlib import Path

import streamlit as st

from src.app_logic import select_result_view
from src.image_source import download_public_image
from src.v2_multiclass_e8_inference import load_e8_config, load_e8_model, predict_e8_image
from src.v2_multilabel_e7_inference import load_e7_config, load_e7_model, predict_e7_image


ROOT = Path(__file__).resolve().parent
PHASE_1_MODEL_PATH = ROOT / "artifacts" / "v2_e8_efficientnetb0_low_lr_best.keras"
PHASE_1_CONFIG_PATH = ROOT / "artifacts" / "v2_multiclass_e8_config.json"
PHASE_2_MODEL_PATH = ROOT / "artifacts" / "e7_focused_best.keras"
PHASE_2_CONFIG_PATH = ROOT / "artifacts" / "v2_multilabel_e7_config.json"
HF_MODEL_REPOSITORY = "FF2050/gov-01-road-damage-classifier-model"

st.set_page_config(
    page_title="GOV-01 Road Condition Checker",
    layout="centered",
)


def _local_or_hosted_model(local_path: Path, filename: str) -> Path:
    """Use a local artifact for development or download the published artifact."""
    if local_path.is_file():
        return local_path
    from huggingface_hub import hf_hub_download
    try:
        return Path(hf_hub_download(
            repo_id=HF_MODEL_REPOSITORY,
            filename=filename,
        ))
    except Exception as exc:
        raise FileNotFoundError(
            f"The published model file '{filename}' could not be downloaded "
            f"({type(exc).__name__})."
        ) from exc


@st.cache_resource(show_spinner="Loading Phase 1: one main class...")
def get_phase_1_artifacts():
    config = load_e8_config(PHASE_1_CONFIG_PATH)
    return load_e8_model(_local_or_hosted_model(PHASE_1_MODEL_PATH, config["model_file"])), config


@st.cache_resource(show_spinner="Loading Phase 2: all road conditions...")
def get_phase_2_artifacts():
    config = load_e7_config(PHASE_2_CONFIG_PATH)
    return load_e7_model(_local_or_hosted_model(PHASE_2_MODEL_PATH, config["model_file"])), config


st.title("GOV-01 Road Condition Checker")
st.caption("Choose a road image from your device or use a direct public image link")

st.info(
    "The app first checks how many Phase 2 conditions meet their locked thresholds. "
    "It then shows one appropriate result: Phase 1 for zero or one condition, or "
    "Phase 2 for two or more conditions. It only predicts; it never trains or changes either model."
)

source_choice = st.radio(
    "Choose an image source",
    ["Upload from device", "Use an image URL"],
    horizontal=True,
)

selected_image = None
if source_choice == "Upload from device":
    selected_image = st.file_uploader(
        "Upload a road image",
        type=["jpg", "jpeg", "png"],
        help="Use a readable PNG or JPEG image of a road scene.",
    )
    if selected_image is not None:
        st.image(selected_image, caption="Selected image (preview)", width=240)
    analyze_requested = st.button(
        "Analyze road image",
        type="primary",
        use_container_width=True,
        disabled=selected_image is None,
    )
else:
    image_url = st.text_input(
        "Direct public JPG or PNG link",
        placeholder="https://example.org/road-photo.jpg",
        help="Paste the final JPG or PNG file address, not a web-page address. The image must be public and at most 10 MB.",
    )
    analyze_requested = st.button(
        "Analyze road image",
        type="primary",
        use_container_width=True,
        disabled=not image_url.strip(),
    )
    if analyze_requested:
        try:
            selected_image = download_public_image(image_url)
        except ValueError as exc:
            st.error(str(exc))

if selected_image is not None and analyze_requested:
    st.image(
        selected_image,
        caption="Selected image (preview)",
        width=240,
    )
    try:
        phase_2_model, phase_2_config = get_phase_2_artifacts()
        phase_2_result = predict_e7_image(
            selected_image, model=phase_2_model, config=phase_2_config
        )
        result_view = select_result_view(phase_2_result["detected_conditions"])

        st.divider()
        if result_view == "one_condition":
            phase_1_model, phase_1_config = get_phase_1_artifacts()
            phase_1_result = predict_e8_image(
                selected_image, model=phase_1_model, config=phase_1_config
            )
            st.subheader("Phase 1 — one main road condition")
            st.metric(
                phase_1_result["prediction"]["condition"],
                f"{phase_1_result['prediction']['probability']:.1%} confidence",
            )
            st.caption(
                "Phase 2 found zero or one condition at its locked thresholds, so the app shows "
                "the Phase 1 single-class result. A person must still confirm it."
            )
        else:
            st.subheader("Phase 2 — all detected road conditions")
            detected = phase_2_result["detected_conditions"]
            st.warning("Detected: " + ", ".join(detected))
            st.dataframe(
                [
                    {
                        "Condition": score["condition"],
                        "Probability": f"{score['probability']:.1%}",
                        "Threshold": f"{score['threshold']:.0%}",
                        "Detected": "Yes" if score["detected"] else "No",
                    }
                    for score in phase_2_result["scores"]
                ],
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "Two or more Phase 2 conditions met their locked thresholds, so the app shows only "
                "the multi-condition result. A person must still confirm it."
            )
    except (FileNotFoundError, ValueError, ImportError) as exc:
        st.error(str(exc))

st.divider()
st.subheader("Important limitation")
st.write(
    "These image-classification models support report triage only. They do not determine "
    "physical size, severity, danger, repair cost, repair priority, or road safety. "
    "Phase 3 area outlines are not available yet."
)
st.caption("Phase 1: V2-E8 EfficientNetB0 | Phase 2: locked V2 multi-label E7")
