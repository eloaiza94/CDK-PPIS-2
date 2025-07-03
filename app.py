import streamlit as st 
import pandas as pd

st.set_page_config(page_title="Estimate vs CDK Cross-Reference", layout="wide")

# 🔤 Add Orbitron font for futuristic vibe
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# 🎨 Apply neon cyberpunk CSS with your Cyber Samurai Alley wallpaper
st.markdown("""
<style>
body {
    background: url('https://images.unsplash.com/photo-1580810736704-10f50c43e89e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80') no-repeat center center fixed;
    background-size: cover;
}

/* optional dark overlay to improve text readability */
body::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.6); /* adjust darkness if needed */
    z-index: -1;
}

h1, h2, h3, h4 {
    font-family: 'Orbitron', sans-serif;
    color: #00ffff;
    text-shadow: 0 0 10px #00ffff, 0 0 20px #ff00ff;
    text-align: center;
}

.stApp {
    font-family: 'Orbitron', sans-serif;
    color: #e0e0e0;
}

.stTextInput, .stTextArea, .stFileUploader {
    border-radius: 10px;
    background-color: rgba(30, 30, 30, 0.8);
    color: #00ffff;
    box-shadow: 0 0 20px rgba(0,255,255,0.5);
    transition: box-shadow 0.4s, transform 0.4s;
}

.stTextInput:focus, .stTextArea:focus, .stFileUploader:focus {
    box-shadow: 0 0 40px rgba(255,0,255,0.7);
    transform: scale(1.02);
}

.stButton > button {
    background: linear-gradient(135deg, #ff00ff, #00ffff);
    color: #000000;
    font-weight: bold;
    border-radius: 8px;
    text-shadow: 0 0 5px #00ffff;
    box-shadow: 0 0 20px rgba(255,0,255,0.7);
    transition: transform 0.3s, box-shadow 0.3s;
}

.stButton > button:hover {
    transform: scale(1.1);
    box-shadow: 0 0 40px rgba(0,255,255,0.9);
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Estimate vs CDK Cross-Reference Tool ⚡")
st.write("Upload your estimate Excel file and paste your CDK parts list below. Get a detailed match report instantly—cyberpunk style!")

estimate_file = st.file_uploader("Upload Estimate Excel", type=["xlsx"])
cdk_text = st.text_area("Paste CDK Parts List", height=300)

if st.button("Generate Match Report") and estimate_file and cdk_text.strip():
    with st.spinner("Processing your neon match report..."):

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

        st.success("⚡ Your neon match report is ready!")
        st.dataframe(match_df, use_container_width=True)

        csv = match_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report as CSV", csv, "match_report.csv", "text/csv")
