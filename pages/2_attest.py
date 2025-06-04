import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os

EXCEL_FILE = "protocol_sections.xlsx"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ROW_SELECTION_FILE = "protocol_row_map.csv"
ATTEST_LOG = "attestations.csv"

st.set_page_config(
    page_title="Protocol Attestation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SITES = ["MMC", "Overlook"]
EMAIL_RECIPIENTS = ["sean.chinery@atlantichealth.org"]

# Load active protocols
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("No active protocols selected. Please go to Home and choose protocols.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()

# Load row filters (optional)
ROWCOL_SELECTION_FILE = "protocol_row_col_map.csv"

if os.path.exists(ROWCOL_SELECTION_FILE):
    rowcol_df = pd.read_csv(ROWCOL_SELECTION_FILE)
else:
    rowcol_df = pd.DataFrame(columns=["Protocol", "RowIndex", "OriginalColumn", "RenamedColumn"])

st.title("✅ CT Protocol Attestation Form")
st.markdown("Please review only the rows selected for each protocol and confirm your attestation.")

try:
    xl = pd.ExcelFile(EXCEL_FILE)
except FileNotFoundError:
    st.error(f"Excel file '{EXCEL_FILE}' not found.")
    st.stop()

completed = {}

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")
    if protocol not in xl.sheet_names:
        st.warning(f"'{protocol}' not found in Excel file.")
        continue

    df = xl.parse(protocol)

    # Filter rows if mapping exists
    rows_for_protocol = row_map[row_map["Protocol"] == protocol]["RowIndex"].tolist()
    if rows_for_protocol:
        df = df.iloc[[i - 1 for i in rows_for_protocol if 1 <= i <= len(df)]]

    st.dataframe(df, use_container_width=True)
    completed[protocol] = st.checkbox(f"✅ Mark '{protocol}' as completed", key=protocol)

st.markdown("---")
st.subheader("🖊 Final Attestation")

name = st.text_input("Supervisor Name")
site = st.selectbox("Select Site", SITES)
confirm = st.checkbox("I attest that I have reviewed and am responsible for the protocols above.")

if st.button("Submit Attestation"):
    if not name or not site or not confirm:
        st.warning("Please complete all fields and confirm.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        done = [p for p in completed if completed[p]]
        not_done = [p for p in completed if not completed[p]]

        new_entry = {
            "Timestamp": timestamp,
            "Name": name,
            "Site": site,
            "Completed Protocols": "; ".join(done),
            "Incomplete Protocols": "; ".join(not_done)
        }

        try:
            df = pd.read_csv(ATTEST_LOG)
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([new_entry])
        df.to_csv(ATTEST_LOG, index=False)

        try:
            msg = EmailMessage()
            msg["Subject"] = f"[CT Attestation] {name} from {site}"
            msg["From"] = "noreply@protocolattestation.app"
            msg["To"] = ", ".join(EMAIL_RECIPIENTS)

            msg.set_content(f"""
Supervisor: {name}
Site: {site}
Timestamp: {timestamp}

✅ Completed Protocols:
{chr(10).join(done) if done else 'None'}

❌ Not Marked Complete:
{chr(10).join(not_done) if not_done else 'None'}
""")

            # SMTP block is optional and commented out
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login("sean.chinery@gmail.com", "jlgu hwjl ucth nkkp")
                server.send_message(msg)

            st.success("✅ Attestation recorded. Email template prepared.")
            #st.info("Email sending is currently disabled (uncomment SMTP to enable).")
        except Exception as e:
            st.warning(f"Attestation saved, but email failed to send: {e}")
