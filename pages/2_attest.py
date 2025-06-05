import streamlit as st
import pandas as pd
import os
import datetime
import textwrap
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Protocol Attestation", layout="wide", initial_sidebar_state="collapsed")
st.title("✅ Protocol Attestation")

# Constants
EXCEL_FILE = "protocol_sections.xlsx"
ROWCOL_SELECTION_FILE = "protocol_row_col_map.csv"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ATTEST_LOG = "attestation_log.csv"
SHEET_IMAGES_DIR = "sheet_images"

# Load necessary files
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please select protocols on the home page.")
    st.stop()

if not os.path.exists(ROWCOL_SELECTION_FILE):
    st.warning("No row/column selections found. Please complete 'Choose Rows and Columns' first.")
    st.stop()

try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

# Inputs
site = st.selectbox("Select your site:", ["MMC", "Overlook"])
name = st.text_input("Your full name:")

# Load dataframes
active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
rowcol_df = pd.read_csv(ROWCOL_SELECTION_FILE)
active_protocols = active_df["Protocol"].tolist()

# Collect completed protocols
finished_protocols = []

st.markdown("### 📋 Review and confirm protocol changes below.")

for protocol in active_protocols:
    st.markdown(f"---\n#### 📄 {protocol}")
    
    try:
        df = xl.parse(protocol)
    except:
        st.error(f"Could not load sheet for {protocol}")
        continue

    selection = rowcol_df[rowcol_df["Protocol"] == protocol]
    if df.empty or selection.empty:
        st.info("No matching data found.")
        continue

    # Show optional description
    descriptions = selection["Description"].dropna().unique()
    if len(descriptions) > 0:
        st.markdown(f"**Change Description:** {descriptions[0]}")

    selected_rows = selection["RowIndex"].unique().tolist()
    col_map = selection[["OriginalColumn", "RenamedColumn"]].drop_duplicates()
    rename_dict = dict(zip(col_map["OriginalColumn"], col_map["RenamedColumn"]))
    display_cols = list(rename_dict.keys())

    try:
        df_display = df.loc[selected_rows, display_cols].rename(columns=rename_dict)
    except Exception as e:
        st.error(f"Error displaying table for {protocol}: {e}")
        continue

    if df_display.columns.duplicated().any():
        st.error(f"Duplicate renamed columns found in {protocol}.")
        continue

    st.dataframe(df_display, use_container_width=True)

    # Show sheet snapshot image if available
    img_path = os.path.join(SHEET_IMAGES_DIR, f"{protocol}.png")
    if os.path.exists(img_path):
        st.image(Image.open(img_path), caption=f"{protocol} snapshot", use_column_width=True)

    if st.checkbox(f"I confirm {protocol} has been updated", key=f"{protocol}_done"):
        finished_protocols.append(protocol)

# Submit
if st.button("📨 Submit Attestation"):
    if not name or not site:
        st.error("Please enter your name and site.")
        st.stop()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unchecked = [p for p in active_protocols if p not in finished_protocols]

    log_entry = {
        "Name": name,
        "Site": site,
        "Timestamp": timestamp,
        "Protocols Reviewed": ", ".join(active_protocols),
        "Protocols Completed": ", ".join(finished_protocols),
    }

    # Append to log
    df_log = pd.DataFrame([log_entry])
    if os.path.exists(ATTEST_LOG):
        existing = pd.read_csv(ATTEST_LOG)
        df_log = pd.concat([existing, df_log], ignore_index=True)
    df_log.to_csv(ATTEST_LOG, index=False)
    st.success("Your attestation has been recorded.")

    # Prepare email
    recipients = ["sean.chinery@atlantichealth.org"]
    sender = "your.email@gmail.com"
    subject = f"Protocol Attestation Submitted by {name}"

    body_lines = [
        f"Supervisor: {name}",
        f"Site: {site}",
        f"Timestamp: {timestamp}",
        "",
        "✅ Completed Protocols:"
    ]
    body_lines += [f"{p}" for p in finished_protocols] if finished_protocols else ["None"]
    body_lines += ["", "❌ Not Marked Complete:"]
    body_lines += [f"{p}" for p in unchecked] if unchecked else ["None"]
    body = "\n".join(body_lines)

    # Send email
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("sean.chinery@gmail.com", "agwv sdua yywu lqmr")  # replace with real app password
            server.sendmail(sender, recipients, msg.as_string())
        st.info("Confirmation email sent.")
    except Exception as e:
        st.warning(f"Failed to send email: {e}")
