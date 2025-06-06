import streamlit as st
import pandas as pd
from PIL import Image
from collections import Counter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import storage
from Streamlit_App_Rewrite import EXCEL_FILE, SHEET_IMAGES_DIR
from datetime import datetime, timedelta



st.set_page_config(
    page_title="Protocol Attestation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("✅ Protocol Attestation")

# Load active protocols
active_df = storage.get_active_protocols()
if active_df.empty or "protocol" not in active_df.columns:
    st.warning("Please select protocols on the home page.")
    st.stop()

active_protocols = active_df["protocol"].dropna().tolist()
if not active_protocols:
    st.warning("No protocols selected.")
    st.stop()

# Load row/column selection map
rowcol_df = storage.get_row_col_map()
rowcol_df.columns = [c.lower() for c in rowcol_df.columns]

# Load Excel workbook
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

# Load site list from local CSV (not Supabase)
SITE_LIST_FILE = "site_list.csv"
if os.path.exists(SITE_LIST_FILE):
    site_df = pd.read_csv(SITE_LIST_FILE)
    site_list = site_df["Site"].dropna().unique().tolist()
else:
    site_list = ["MMC", "Overlook"]

# Supervisor input
st.markdown("### 🧑‍⚕️ Attesting Supervisor Info")
site = st.selectbox("Select your site:", site_list)
name = st.text_input("Your full name:")
description = st.text_area("Optional notes about these protocol changes:")

# Protocol confirmations
st.markdown("### 📋 Review and confirm protocol changes below.")
finished_protocols = []

for protocol in active_protocols:
    st.markdown(f"---\n#### 📄 {protocol}")
    try:
        df = xl.parse(protocol)
    except Exception as e:
        st.warning(f"Could not load sheet for {protocol}: {e}")
        continue
    
    selection = rowcol_df[rowcol_df["protocol"] == protocol]

    if df.empty or selection.empty:
        st.info("No matching data found.")
        continue

    rename_row = selection["rename_row"].iloc[0] if "rename_row" in selection.columns else 0
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

    selected_rows = selection["row_index"].unique().tolist()
    display_cols = selection["original_column"].unique().tolist()

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

    protocol_notes = selection["description"].dropna().unique().tolist()
    if protocol_notes:
        st.markdown(f"**Notes:** {protocol_notes[0]}")

    checked = st.checkbox(f"I confirm {protocol} has been updated", key=f"{protocol}_done")
    if checked:
        finished_protocols.append(protocol)

# Submit and email
if st.button("📨 Submit Attestation"):
    if not name or not site:
        st.error("Please enter your name and site.")
        st.stop()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "name": name,
        "site": site,
        "timestamp": timestamp,
        "protocols_reviewed": ", ".join(active_protocols),
        "protocols_completed": ", ".join(finished_protocols),
        "description": description
    }

    try:
        storage.append_attestation_log(entry)
        st.success("Your attestation has been recorded.")
    except Exception as e:
        st.error(f"Failed to save attestation: {e}")
        st.stop()

    # Send confirmation email
    recipients = ["sean.chinery@atlantichealth.org"]
    sender = "your.email@gmail.com"
    subject = f"Protocol Attestation Submitted by {name}"
    unchecked = [p for p in active_protocols if p not in finished_protocols]

    body_lines = [
        f"Supervisor: {name}",
        f"Site: {site}",
        f"Timestamp: {timestamp}",
        "",
        f"Notes: {description if description else 'None'}",
        "",
        "✅ Completed Protocols:"
    ]
    body_lines += [f"  {p}" for p in finished_protocols] if finished_protocols else ["  None"]
    body_lines += ["", "❌ Not Marked Complete:"]
    body_lines += [f"  {p}" for p in unchecked] if unchecked else ["  None"]

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
