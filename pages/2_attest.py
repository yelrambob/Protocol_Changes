import streamlit as st
import pandas as pd
import os
import datetime
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import Counter

### Import shared paths
from Streamlit_App_Rewrite import (
    EXCEL_FILE,
    ROWCOL_SELECTION_FILE,
    ACTIVE_PROTOCOLS_FILE,
    ATTEST_LOG,
    SHEET_IMAGES_DIR,
    SITE_LIST_FILE
)

st.set_page_config(
    page_title="Protocol Changes and Confirmation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("✅ Protocol Changes and Confirmation of Change")

# 🔍 DEBUG BLOCK
st.sidebar.subheader("Debug Info")
st.sidebar.write("ACTIVE_PROTOCOLS_FILE path:", ACTIVE_PROTOCOLS_FILE)
st.sidebar.write("Exists?", os.path.exists(ACTIVE_PROTOCOLS_FILE))

# Load data
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please select protocols on the home page.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
st.sidebar.write("Loaded protocols:", active_df)

if "Protocol" not in active_df.columns or active_df.empty:
    st.warning("Active protocol file is empty or missing 'Protocol' column.")
    st.stop()

active_protocols = active_df["Protocol"].dropna().tolist()
if not active_protocols:
    st.warning("No protocols selected.")
    st.stop()

if not os.path.exists(ROWCOL_SELECTION_FILE):
    st.warning("No row/column selections found. Please complete 'Choose Rows and Columns' first.")
    st.stop()

rowcol_df = pd.read_csv(ROWCOL_SELECTION_FILE)

try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

# Supervisor info
st.markdown("### 🧑‍⚕️ Attesting Supervisor Info")
if os.path.exists(SITE_LIST_FILE):
    site_list = pd.read_csv(SITE_LIST_FILE)["Site"].dropna().unique().tolist()
else:
    site_list = ["MMC", "Overlook"]

site = st.selectbox("Select your site:", site_list)
name = st.text_input("Your full name:")

# Optional notes
description = st.text_area("Optional notes about these protocol changes:")

# Protocol review
st.markdown("### 📋 Review and confirm protocol changes below.")
finished_protocols = []

for protocol in active_protocols:
    st.markdown(f"---\n#### 📄 {protocol}")

    try:
        df = xl.parse(protocol)
    except Exception as e:
        st.warning(f"Could not load sheet for {protocol}: {e}")
        continue

    selection = rowcol_df[rowcol_df["Protocol"] == protocol]

    if df.empty or selection.empty:
        st.info("No matching data found.")
        continue

    rename_row = selection["RenameRow"].iloc[0] if "RenameRow" in selection.columns else 0
    if rename_row >= len(df):
        st.warning(f"Invalid rename row for {protocol}. Skipping.")
        continue

    raw_headers = df.iloc[rename_row].astype(str).tolist()
    name_counter = Counter()
    new_headers = []
    for h in raw_headers:
        name_counter[h] += 1
        new_headers.append(f"{h}_{name_counter[h]}" if name_counter[h] > 1 else h)

    df.columns = new_headers
    df = df.iloc[rename_row + 1:].reset_index(drop=True)

    selected_rows = selection["RowIndex"].unique().tolist()
    display_cols = selection["OriginalColumn"].unique().tolist()

    valid_rows = [r for r in selected_rows if r in df.index]
    valid_cols = [c for c in display_cols if c in df.columns]

    if not valid_cols:
        st.info(f"No matching columns in data for {protocol}. Skipping.")
        continue

    df_display = df.loc[valid_rows, valid_cols]
    st.dataframe(df_display, use_container_width=True)

    img_path = os.path.join(SHEET_IMAGES_DIR, f"{protocol}.png")
    if os.path.exists(img_path):
        st.image(Image.open(img_path), caption=f"{protocol} snapshot", use_column_width=True)

    protocol_notes = selection["Description"].dropna().unique().tolist()
    if protocol_notes:
        st.markdown(f"**Notes:** {protocol_notes[0]}")

    checked = st.checkbox(f"I confirm {protocol} has been updated", key=f"{protocol}_done")
    if checked:
        finished_protocols.append(protocol)

# Submit block
if st.button("📨 Submit Attestation"):
    if not name or not site:
        st.error("Please enter your name and site.")
        st.stop()

    log_entry = {
        "Name": name,
        "Site": site,
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Protocols Reviewed": ", ".join(active_protocols),
        "Protocols Completed": ", ".join(finished_protocols),
        "Description": description
    }

    df_log = pd.DataFrame([log_entry])
    if os.path.exists(ATTEST_LOG):
        existing = pd.read_csv(ATTEST_LOG)
        df_log = pd.concat([existing, df_log], ignore_index=True)

    df_log.to_csv(ATTEST_LOG, index=False)
    st.success("Your attestation has been recorded.")

    # Email notification
    recipients = ["sean.chinery@atlantichealth.org"]
    sender = "your.email@gmail.com"
    subject = f"Protocol Attestation Submitted by {name}"

    unchecked = [p for p in active_protocols if p not in finished_protocols]

    body_lines = [
        f"Supervisor: {name}",
        f"Site: {site}",
        f"Timestamp: {log_entry['Timestamp']}",
        "",
        f"Notes: {description or 'None'}",
        "",
        "✅ Completed Protocols:",
        *(f"  {p}" for p in finished_protocols or ["None"]),
        "",
        "❌ Not Marked Complete:",
        *(f"  {p}" for p in unchecked or ["None"])
    ]

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("sean.chinery@gmail.com", "agwv sdua yywu lqmr")
            server.sendmail(sender, recipients, msg.as_string())
        st.info("Confirmation email sent.")
    except Exception as e:
        st.warning(f"Failed to send email: {e}")
