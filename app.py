import streamlit as st 
import pandas as pd
import re
from fpdf import FPDF
from io import BytesIO
import base64

st.set_page_config(page_title="Estimate vs CDK Cross-Reference", layout="wide")  # switched to wide mode

st.markdown(
    """
    <style>
    body {
        background-color: #1e1e1e;
        color: #e0e0e0;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stApp {
        max-width: 100%; /* Stretch to full page width */
        width: 100%;
        margin: 0 auto;
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #f5f5f5;
        text-align: center;
    }
    .stButton>button {
        background-color: #0a84ff;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #0066cc;
        transform: scale(1.05);
    }
    .stTextInput>div>div>input {
        background-color: #2c2c2c;
        color: #e0e0e0;
        border: none;
        border-radius: 6px;
        padding: 0.5em;
    }
    .stTextInput>div>div>input:focus {
        outline: 2px solid #0a84ff;
    }
    .stMarkdown p {
        font-size: 1.1em;
        line-height: 1.6;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Estimate vs CDK Cross-Reference Tool")
st.write("Upload your estimate Excel file and paste your CDK parts list below. Get a detailed match report instantly!")

estimate_file = st.file_uploader("Upload Estimate Excel", type=["xlsx"])
cdk_text = st.text_area("Paste CDK Parts List", height=300)

if st.button("Generate Match Report") and estimate_file and cdk_text.strip():
    with st.spinner("Processing..."):

        estimate_df = pd.read_excel(estimate_file)
        estimate_clean = estimate_df.copy()
        estimate_clean = estimate_clean[estimate_clean["Part Number"].notnull()]
        estimate_clean = estimate_clean[estimate_clean["Part Number"].astype(str).str.strip() != "-"]
        estimate_clean["Part Number"] = estimate_clean["Part Number"].apply(
            lambda x: str(int(x)) if pd.notnull(x) and isinstance(x, (int, float)) else str(x).strip())
        estimate_clean["Quantity"] = estimate_clean["Quantity"].fillna(0).astype(int)

        cdk_lines = []
        for line in cdk_text.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 4:
                part_no, qty, description, price = parts[0], parts[1],_
