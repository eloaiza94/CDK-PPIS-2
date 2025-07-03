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
                part_no, qty, description, price = parts[0], parts[1], " ".join(parts[2:-1]), parts[-1]
                try:
                    cdk_lines.append({
                        "Part Number": part_no.strip(),
                        "CDK Quantity": int(qty.strip()),
                        "CDK Description": description.strip(),
                        "CDK Price": float(price.replace(",", "").strip()),
                    })
                except ValueError:
                    continue
        cdk_df = pd.DataFrame(cdk_lines)

        matches = []
        for _, est in estimate_clean.iterrows():
            est_part = est["Part Number"]
            est_qty = est["Quantity"]
            est_price = est["Extended Price"]
            cdk_match = cdk_df[cdk_df["Part Number"] == est_part]

            if not cdk_match.empty:
                cdk_row = cdk_match.iloc[0]
                if est_qty == cdk_row["CDK Quantity"] and abs(est_price - cdk_row["CDK Price"]) < 0.01:
                    match_status = "Matched by Part #, Qty & Price"
                elif est_qty == cdk_row["CDK Quantity"]:
                    match_status = "Matched by Part # & Qty"
                elif abs(est_price - cdk_row["CDK Price"]) < 0.01:
                    match_status = "Matched by Part # & Price"
                else:
                    match_status = "Matched by Part # Only"
                matches.append({
                    "Estimate Line #": est["Line"],
                    "Part Number": est_part,
                    "Description": est["Description"],
                    "Estimate Quantity": est_qty,
                    "CDK Quantity": cdk_row["CDK Quantity"],
                    "Estimate Price": est_price,
                    "CDK Price": cdk_row["CDK Price"],
                    "Match Report": match_status
                })
            else:
                matches.append({
                    "Estimate Line #": est["Line"],
                    "Part Number": est_part,
                    "Description": est["Description"],
                    "Estimate Quantity": est_qty,
                    "CDK Quantity": None,
                    "Estimate Price": est_price,
                    "CDK Price": None,
                    "Match Report": "❌ Missing in CDK"
                })

        for _, cdk in cdk_df.iterrows():
            cdk_part = cdk["Part Number"]
            est_match = estimate_clean[estimate_clean["Part Number"] == cdk_part]
            if est_match.empty:
                matches.append({
                    "Estimate Line #": "-",
                    "Part Number": cdk_part,
                    "Description": cdk["CDK Description"],
                    "Estimate Quantity": None,
                    "CDK Quantity": cdk["CDK Quantity"],
                    "Estimate Price": None,
                    "CDK Price": cdk["CDK Price"],
                    "Match Report": "❌ Missing in Estimate"
                })

        match_df = pd.DataFrame(matches)

        def color_code_status(row):
            if row["Match Report"] == "Matched by Part #, Qty & Price":
                return "✅ Perfect Match"
            elif "Missing" in row["Match Report"]:
                return "❌ No Match"
            else:
                return "🛠️ PPI Needed"

        match_df["Color Coded Match Report"] = match_df.apply(color_code_status, axis=1)

        st.success("Match Report Generated!")
        st.dataframe(match_df, use_container_width=True)

        csv = match_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report as CSV", csv, "match_report.csv", "text/csv")

        # 📧 Estimator email
        missing_estimate_lines = match_df[
            (match_df["Match Report"] == "❌ Missing in Estimate") &
            (~match_df["Description"].str.contains("RFC", case=False, na=False))
        ]
        if not missing_estimate_lines.empty:
            first_email = (
                "Hey Deshunn can you look into these for me please they're billed out "
                "and I want to see if they're supposed to be on the estimate:\n\n"
            )
            for _, row in missing_estimate_lines.iterrows():
                price_str = f"${row['CDK Price']:.2f}" if pd.notnull(row["CDK Price"]) else "N/A"
                first_email += f"- {row['Part Number']} | {row['Description']} | {price_str}\n"
            st.subheader("📩 Email for Estimator (Missing in Estimate):")
            st.code(first_email, language="markdown")
        else:
            st.info("No 'Missing in Estimate' items found for estimator email.")

        # 📧 Parts department email
        second_email = ""
        rfc_lines = match_df[
            (match_df["Description"].str.contains("RFC", case=False, na=False)) &
            (match_df["Match Report"] == "❌ Missing in Estimate")
        ]
        if not rfc_lines.empty:
            second_email += "Can we get these taken off of the ticket please:\n\n"
            for _, row in rfc_lines.iterrows():
                price_str = f"${row['CDK Price']:.2f}" if pd.notnull(row["CDK Price"]) else "N/A"
                qty_str = f"{row['CDK Quantity']}" if pd.notnull(row["CDK Quantity"]) else "N/A"
                second_email += f"- {row['Part Number']} | {row['Description']} | {price_str} | Qty: {qty_str}\n"

        second_email += "\n\n\n"

        missing_cdk_lines = match_df[match_df["Match Report"] == "❌ Missing in CDK"]
        if not missing_cdk_lines.empty:
            second_email += (
                "Also can you look into these for me and let me know if we forgot to bill them out please:\n\n"
            )
            for _, row in missing_cdk_lines.iterrows():
                price_str = f"${row['Estimate Price']:.2f}" if pd.notnull(row["Estimate Price"]) else "N/A"
                second_email += f"- {row['Part Number']} | {row['Description']} | {price_str}\n"

        if second_email.strip() != "":
            st.subheader("📩 Email for Parts Department (RFC + Missing in CDK):")
            st.code(second_email, language="markdown")
        else:
            st.info("No RFC or 'Missing in CDK' items found for parts email.")

        # ✅ Create possible matches report: estimate lines missing in CDK but qty+price match
        possible_matches = []
        for _, est_row in match_df[match_df["Match Report"] == "❌ Missing in CDK"].iterrows():
            est_qty = est_row["Estimate Quantity"]
            est_price = est_row["Estimate Price"]

            candidates = cdk_df[
                (cdk_df["CDK Quantity"] == est_qty) &
                (abs(cdk_df["CDK Price"] - est_price) < 0.01)
            ]
            for _, cdk_row in candidates.iterrows():
                possible_matches.append({
                    "Estimate Line #": est_row["Estimate Line #"],
                    "Est Part #": est_row["Part Number"],
                    "Est Qty": est_qty,
                    "Est Price": est_price,
                    "Est Description": est_row["Description"],
                    "CDK Part #": cdk_row["Part Number"],
                    "CDK Qty": cdk_row["CDK Quantity"],
                    "CDK Price": cdk_row["CDK Price"],
                    "CDK Description": cdk_row["CDK Description"]
                })

        if possible_matches:
            possible_matches_df = pd.DataFrame(possible_matches)
            st.subheader("🔍 Possible Matches Based on Qty & Price:")
            st.dataframe(possible_matches_df, use_container_width=True)
        else:
            st.info("No possible matches found based on qty & price.")
