"""Local Streamlit demo for the locked GOV-01 pothole classifier."""

from pathlib import Path

import streamlit as st

from src.inference import load_artifact_config, load_saved_model, predict_image


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "artifacts" / "mobilenetv2_frozen_v4.keras"
CONFIG_PATH = ROOT / "artifacts" / "mobilenetv2_frozen_v4_config.json"

st.set_page_config(
    page_title="GOV-01 Road Damage Classifier",
    layout="centered",
)


@st.cache_resource(show_spinner="Loading the saved V4 model...")
def get_artifacts():
    """Load model and configuration once for the current Streamlit process."""
    return load_saved_model(MODEL_PATH), load_artifact_config(CONFIG_PATH)


st.title("GOV-01 Road Damage Classifier")
st.caption("Local demo: one road image -> Normal or Pothole")

st.info(
    "This demo loads the final saved model and predicts one new image. "
    "It does not train or change the model."
)

try:
    model, config = get_artifacts()
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

uploaded_image = st.file_uploader(
    "Upload a road image",
    type=["jpg", "jpeg", "png"],
    help="Use a readable PNG or JPEG image of a road scene.",
)

if uploaded_image is not None:
    st.image(uploaded_image, caption="Selected image", use_container_width=True)

    if st.button("Classify image", type="primary", use_container_width=True):
        try:
            result = predict_image(uploaded_image, model=model, config=config)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.divider()
            st.subheader("Prediction result")
            left, right = st.columns(2)
            left.metric("Prediction", result["label"])
            right.metric(
                "Pothole probability",
                f"{result['pothole_probability']:.1%}",
            )

            if result["label"] == "Pothole":
                st.warning("Potential pothole detected. Send this report for human review.")
            else:
                st.success("No pothole detected by the model. Human review is still required.")

st.divider()
st.subheader("Important limitation")
st.write(
    "The model detects pothole presence only. It does not determine pothole "
    "danger, physical size, severity, repair cost, or repair priority."
)
st.caption("Selected model: mobilenetv2_frozen_v4 | Decision threshold: 0.5")
