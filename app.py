"""One-upload Streamlit interface for GOV-01 Phases 1 and 2."""

from pathlib import Path

import streamlit as st

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
st.caption("One uploaded road image → Phase 1 and Phase 2 results")

st.info(
    "One image is checked by two locked models. The app only predicts; it does not train, "
    "change thresholds, or alter either model."
)

try:
    phase_1_model, phase_1_config = get_phase_1_artifacts()
    phase_2_model, phase_2_config = get_phase_2_artifacts()
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

uploaded_image = st.file_uploader(
    "Upload a road image",
    type=["jpg", "jpeg", "png"],
    help="Use a readable PNG or JPEG image of a road scene.",
)

if uploaded_image is not None:
    st.image(
        uploaded_image,
        caption="Selected image (compact preview)",
        width=240,
    )
    st.caption(
        "This preview is only for checking the selected image."
    )

    if st.button("Analyze road image", type="primary", use_container_width=True):
        try:
            phase_1_result = predict_e8_image(
                uploaded_image, model=phase_1_model, config=phase_1_config
            )
            phase_2_result = predict_e7_image(
                uploaded_image, model=phase_2_model, config=phase_2_config
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.divider()
            st.subheader("Phase 1 — one main road condition")
            st.metric(
                phase_1_result["prediction"]["condition"],
                f"{phase_1_result['prediction']['probability']:.1%} confidence",
            )
            st.caption("Phase 1 always chooses one class: the most likely of its seven classes.")

            st.subheader("Phase 2 — all detected road conditions")
            detected = phase_2_result["detected_conditions"]
            if detected:
                st.warning("Detected: " + ", ".join(detected))
            else:
                st.success("No Phase 2 condition reached its locked threshold.")
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
            st.info(
                "The two phases answer different questions. Phase 1 must select one main class; "
                "Phase 2 can select several. A qualified person must confirm every result."
            )

st.divider()
st.subheader("Important limitation")
st.write(
    "These image-classification models support report triage only. They do not determine "
    "physical size, severity, danger, repair cost, repair priority, or road safety. "
    "Phase 3 area outlines are not available yet."
)
st.caption("Phase 1: V2-E8 EfficientNetB0 | Phase 2: locked V2 multi-label E7")
