import streamlit as st
import pandas as pd
import os
import datetime
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(
    page_title="Protocol Attestation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

EXCEL_FILE = "protocol_sections.xlsx"
ROWCOL_SELECTION_FILE = "protocol_row_col_map.csv"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ATTEST_LOG = "attestation_log.csv"
SHEET_IMAGES_DIR = "sheet_images"
SITE_LIST_FILE = "site_list.csv"

st.title("✅ Protocol Attestation")

# Load data
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please select protocols on the home page.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()

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

site = st.selectbox("Select your site:", site_list)\nname = st.text_input("Your full name:")

# Optional overall description
description = st.text_area("Optional notes about these protocol changes:")

# Protocol confirmation
st.markdown("### 📋 Review and confirm protocol changes below.")
finished_protocols = []

for protocol in active_protocols:
    st.markdown(f"---\n#### 📄 {protocol}")

    df = xl.parse(protocol)
    selection = rowcol_df[rowcol_df["Protocol"] == protocol]

    if df.empty or selection.empty:
        st.info("No matching data found.")
        continue

    rename_row = selection["RenameRow"].iloc[0] if "RenameRow" in selection.columns else 0
    if rename_row >= len(df):
        st.warning(f"Invalid rename row for {protocol}. Skipping.")
        continue

    raw_headers = df.iloc[rename_row].astype(str).tolist()
    from collections import Counter
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

    checked = st.checkbox(f"I confirm {protocol} has been updated", key=f"{protocol}_done")
    if checked:
        finished_protocols.append(protocol)

# Submit
if st.button("📨 Submit Attestation"):
    if not name or not site:
        st.error("Please enter your name and site.")
        st.stop()

    protocol_list = ", ".join(active_protocols)
    done_list = ", ".join(finished_protocols)

    log_entry = {
        "Name": name,
        "Site": site,
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Protocols Reviewed": protocol_list,
        "Protocols Completed": done_list,
        "Description": description
    }

    df_log = pd.DataFrame([log_entry])
    if os.path.exists(ATTEST_LOG):
        existing = pd.read_csv(ATTEST_LOG)
        df_log = pd.concat([existing, df_log], ignore_index=True)

    df_log.to_csv(ATTEST_LOG, index=False)
    st.success("Your attestation has been recorded.")

    recipients = ["sean.chinery@atlantichealth.org", "dummy@example.com"]
    sender = "your.email@gmail.com"
    subject = f"Protocol Attestation Submitted by {name}"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unchecked = [p for p in active_protocols if p not in finished_protocols]

    body_lines = [
        f"Supervisor: {name}",
        f"Site: {site}",
        f"Timestamp: {timestamp}",
        "",
        f"Notes: {description if description else 'None'}",
        "",
        "✅ Completed Protocols:",
    ]
    body_lines += [f"  {p}" for p in finished_protocols] if finished_protocols else ["  None"]
    body_lines += ["", "❌ Not Marked Complete:"]
    body_lines += [f"  {p}" for p in unchecked] if unchecked else ["  None"]

    body = "\n".join(body_lines)
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("sean.chinery@gmail.com", "agwv sdua yywu lqmr")
            server.sendmail(sender, recipients, msg.as_string())
        st.info("Confirmation email sent.")
    except Exception as e:
        st.warning(f"Failed to send email: {e}")
