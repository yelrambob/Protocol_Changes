import streamlit as st
import pandas as pd
import os
import datetime
import textwrap
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(
    page_title="Confirmation of Protocol Changes by Site",
    layout="wide",
    initial_sidebar_state="collapsed"
)

EXCEL_FILE = "protocol_sections.xlsx"
ROWCOL_SELECTION_FILE = "protocol_row_col_map.csv"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ATTEST_LOG = "attestation_log.csv"
SHEET_IMAGES_DIR = "sheet_images"

st.title("✅ Confirmation of Protocol Changes by Site")

# Load active protocols
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Title placeholder")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()

# Load row/column selections
if not os.path.exists(ROWCOL_SELECTION_FILE):
    st.warning("No row/column selections found. Please complete 'Choose Rows and Columns' first.")
    st.stop()

rowcol_df = pd.read_csv(ROWCOL_SELECTION_FILE)

# Load Excel workbook
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

# Supervisor info
st.markdown("### 🧑‍⚕️ CT Responsible Party")
SITE_LIST_FILE = "site_list.csv"

if os.path.exists(SITE_LIST_FILE):
    site_df = pd.read_csv(SITE_LIST_FILE)
    site_options = site_df["Site"].dropna().unique().tolist()
else:
    site_options = ["MMC", "Overlook"]  # Fallback

site = st.selectbox("Select your site:", site_options)

name = st.text_input("Your name:")

st.markdown("### 📋 Review and confirm protocol changes below.")
finished_protocols = []

for protocol in active_protocols:
    st.markdown(f"---\n#### 📄 {protocol}")

    df = xl.parse(protocol)
    selection = rowcol_df[rowcol_df["Protocol"] == protocol]

    if df.empty or selection.empty:
        st.info("No matching data found.")
        continue

    selected_rows = selection["RowIndex"].unique().tolist()
    col_map = selection[["OriginalColumn", "RenamedColumn"]].drop_duplicates()
    rename_dict = dict(zip(col_map["OriginalColumn"], col_map["RenamedColumn"]))
    display_cols = list(rename_dict.keys())

    # Filter and rename
    valid_rows = [i for i in selected_rows if i in df.index]
    if not valid_rows:
        st.warning(f"No matching rows found in {protocol}. Skipping.")
        continue
    
    df_display = df.loc[valid_rows, display_cols].rename(columns=rename_dict)


    if df_display.columns.duplicated().any():
        st.error(f"Duplicate renamed columns found in {protocol}. Please ensure all renamed columns are unique.")
        continue

    st.dataframe(df_display, use_container_width=True)

    # Show image if available
    img_path = os.path.join(SHEET_IMAGES_DIR, f"{protocol}.png")
    if os.path.exists(img_path):
        st.image(Image.open(img_path), caption=f"{protocol} snapshot", use_column_width=True)

    # Display description
    description = selection["Description"].iloc[0] if "Description" in selection.columns else ""
    if description:
        st.info(f"**Change Description:** {description}")

    # Completion checkbox
    checked = st.checkbox(f"I confirm {protocol} has been updated", key=f"{protocol}_done")
    if checked:
        finished_protocols.append(protocol)

# Submit
if st.button("📨 Submit Confirmation"):
    if not name or not site:
        st.error("Please enter your name and site.")
        st.stop()

    protocol_list = ", ".join(active_protocols)
    done_list = ", ".join(finished_protocols)

    # Log submission
    log_entry = {
        "Name": name,
        "Site": site,
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Protocols Attested": protocol_list,
        "Protocols Marked Complete": done_list
    }

    df_log = pd.DataFrame([log_entry])

    if os.path.exists(ATTEST_LOG):
        existing = pd.read_csv(ATTEST_LOG)
        df_log = pd.concat([existing, df_log], ignore_index=True)

    df_log.to_csv(ATTEST_LOG, index=False)
    st.success("Your confirmation has been recorded.")

    # Email content
    recipients = ["sean.chinery@atlantichealth.org", "edward.levy@atlantichealth.org"]
    sender = "AMG CT Protocol Changes Made"
    subject = f"Protocol Changes/Confirmation Submitted by {name}"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unchecked = [p for p in active_protocols if p not in finished_protocols]

    body_lines = [
        f"Supervisor: {name}",
        f"Site: {site}",
        f"Timestamp: {timestamp}",
        "",
        "✅ Completed Protocols:"
    ]
    body_lines += [f"{p}" for p in finished_protocols] if finished_protocols else ["None"]

    body_lines += [
        "",
        "❌ Not Marked Complete:"
    ]
    body_lines += [f"{p}" for p in unchecked] if unchecked else ["None"]

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
