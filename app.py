from io import BytesIO
from zipfile import ZipFile
import streamlit as st
import torch
from PIL import Image
from transformers import AutoProcessor, BlipForConditionalGeneration


MODEL_ID = "Salesforce/blip-image-captioning-base"


@st.cache_resource(show_spinner="Loading Model")
def load_model():
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = BlipForConditionalGeneration.from_pretrained(MODEL_ID).eval()
    return processor, model


def caption(image):
    processor, model = load_model()
    inputs = processor(images=image.convert("RGB"), return_tensors="pt")
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=30)
    return processor.decode(output[0], skip_special_tokens=True)


st.title("Generate captions")
mode = st.radio("Mode", ["Single image", "Bulk ZIP"])

if mode == "Single image":
    uploaded = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
    if uploaded and st.button("Generate caption"):
        image = Image.open(uploaded)
        st.image(image)
        st.write(caption(image))
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
                text = caption(image)
                rows.append({"file": name, "caption": text})
        st.dataframe(rows, use_container_width=True)
