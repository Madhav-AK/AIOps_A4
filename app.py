from io import BytesIO
from time import time
from uuid import uuid4
from zipfile import ZipFile
import streamlit as st
import torch
from PIL import Image
from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client import disable_created_metrics, start_http_server
from transformers import AutoProcessor, BlipForConditionalGeneration


MODEL_ID = "Salesforce/blip-image-captioning-base"


@st.cache_resource
def setup_metrics():
    disable_created_metrics()
    image_counter = Counter(
        "images_processed_total",
        "Total images processed",
        ["mode", "session_id"],
    )
    active_requests = Gauge(
        "active_requests", "Number of active requests being processed currently", ["mode"]
    )
    inference_time = Histogram(
        "inference_time_seconds",
        "Inference time per image",
        ["mode"],
        buckets=(0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2),
    )
    image_size = Summary(
        "image_size_bytes", "Uploaded image size in bytes", ["mode"]
    )
    model_loaded = Gauge("model_loaded", "Is the model loaded")
    start_http_server(18000)
    return image_counter, active_requests, inference_time, image_size, model_loaded


IMAGE_COUNTER, ACTIVE_REQUESTS, INFERENCE_TIME, IMAGE_SIZE, MODEL_LOADED = setup_metrics()


@st.cache_resource(show_spinner="Loading Model")
def load_model():
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = BlipForConditionalGeneration.from_pretrained(MODEL_ID).eval()
    MODEL_LOADED.set(1)
    return processor, model


def caption(image, mode, size, session_id):
    ACTIVE_REQUESTS.labels(mode=mode).inc()
    try:
        processor, model = load_model()
        inputs = processor(images=image.convert("RGB"), return_tensors="pt")
        start = time()
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=30)
        INFERENCE_TIME.labels(mode=mode).observe(time() - start)
        IMAGE_COUNTER.labels(mode=mode, session_id=session_id).inc()
        IMAGE_SIZE.labels(mode=mode).observe(size)
        return processor.decode(output[0], skip_special_tokens=True)
    finally:
        ACTIVE_REQUESTS.labels(mode=mode).dec()


st.title("Generate captions")
mode = st.radio("Mode", ["Single image", "Bulk ZIP"])

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())

if mode == "Single image":
    uploaded = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
    if uploaded and st.button("Generate caption"):
        image = Image.open(uploaded)
        st.image(image)
        st.write(caption(image, "single", uploaded.size, st.session_state.session_id))
else:
    uploaded = st.file_uploader("Upload ZIP", type="zip")
    if uploaded and st.button("Generate caption"):
        rows = []
        with ZipFile(uploaded) as files:
            names = [
                name
                for name in files.namelist()
                if name.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            for name in names:
                data = files.read(name)
                image = Image.open(BytesIO(data))
                text = caption(image, "bulk", len(data), st.session_state.session_id)
                rows.append({"file": name, "caption": text})
        st.dataframe(rows, use_container_width=True)
