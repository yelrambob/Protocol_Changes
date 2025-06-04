import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os

EXCEL_FILE = "protocol_sections.xlsx"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ATTEST_LOG = "attestations.csv"

SITES = ["MMC", "Overlook"]
EMAIL_RECIPIENTS = ["sean.chinery@atlantichealth.org"]  # Add more if needed

# Load active protocols
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("No active protocols selected. Please go to Home and choose protocols.")
    st.stop()

try:
    active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
    active_protocols = active_df["Protocol"].tolist()
except Exception as e:
    st.error(f"Failed to load active protocols: {e}")
    st.stop()

st.title("✅ CT Protocol Attestation Form")
st.markdown("Please review each updated protocol and check off the ones that have been successfully implemented.")

# Load Excel
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

    try:
        df = xl.parse(protocol)
        st.dataframe(df, use_container_width=True)
        completed[protocol] = st.checkbox(f"✅ Mark '{protocol}' as completed", key=protocol)
    except Exception as e:
        st.warning(f"Error displaying {protocol}: {e}")

st.markdown("---")
st.subheader("🖊 Final Attestation")

name = st.text_input("Supervisor Name")
site = st.selectbox("Select Site", SITES)
confirm = st.checkbox("I attest that I have reviewed and taken responsibility for the above changes.")

if st.button("Submit Attestation"):
    if not name or not site or not confirm:
        st.warning("Please complete all fields and check the attestation box.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        marked_done = [p for p in completed if completed[p]]
        marked_not_done = [p for p in completed if not completed[p]]

        # Log to CSV
        new_entry = {
            "Timestamp": timestamp,
            "Name": name,
            "Site": site,
            "Completed Protocols": "; ".join(marked_done),
            "Incomplete Protocols": "; ".join(marked_not_done)
        }

        try:
            df = pd.read_csv(ATTEST_LOG)
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([new_entry])
        df.to_csv(ATTEST_LOG, index=False)

        # Send email notification
        try:
            msg = EmailMessage()
            msg["Subject"] = f"[CT Attestation] {name} from {site} submitted protocol updates"
            msg["From"] = "noreply@protocolattestation.app"
            msg["To"] = ", ".join(EMAIL_RECIPIENTS)

            body = f"""
Supervisor: {name}
Site: {site}
Timestamp: {timestamp}

✅ Completed Protocols:
{chr(10).join(marked_done) if marked_done else 'None'}

❌ Not Yet Marked Complete:
{chr(10).join(marked_not_done) if marked_not_done else 'None'}

This submission has been logged in attestations.csv.
            """
            msg.set_content(body)

            # Uncomment and update with working SMTP credentials
            # with smtplib.SMTP("smtp.gmail.com", 587) as server:
            #     server.starttls()
            #     server.login("your_email@gmail.com", "your_app_password")
            #     server.send_message(msg)

            st.success("✅ Attestation submitted and email prepared.")
            st.info("Email sending is currently disabled for testing.")
        except Exception as e:
            st.warning(f"Attestation saved, but email failed to send: {e}")
