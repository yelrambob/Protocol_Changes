import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
st.markdown("Please review the updated protocols and complete the attestation below.")

# Display each protocol sheet as an image
try:
    excel = pd.ExcelFile(EXCEL_FILE)
    for protocol in active_protocols:
        if protocol not in excel.sheet_names:
            st.warning(f"'{protocol}' not found in Excel file.")
            continue
        df = excel.parse(protocol)

        st.markdown(f"### 📄 {protocol}")
        fig, ax = plt.subplots(figsize=(min(12, len(df.columns) * 2), min(0.5 * len(df), 12)))
        ax.axis('off')
        table = ax.table(cellText=df.values,
                         colLabels=df.columns,
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        st.pyplot(fig)
except Exception as e:
    st.error(f"Error rendering sheets: {e}")
    st.stop()

st.markdown("---")
st.subheader("🖊 Attestation")

name = st.text_input("Supervisor Name")
site = st.selectbox("Select Site", SITES)
confirm = st.checkbox("I attest that I have reviewed and will implement the updated protocols listed above.")

if st.button("Submit Attestation"):
    if not name or not confirm:
        st.warning("Please enter your name, select a site, and check the attestation box.")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "Timestamp": timestamp,
            "Name": name,
            "Site": site,
            "Protocols": "; ".join(active_protocols)
        }

        # Log to attestations.csv
        try:
            df = pd.read_csv(ATTEST_LOG)
            df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([entry])
        df.to_csv(ATTEST_LOG, index=False)

        # Send email notification
        try:
            msg = EmailMessage()
            msg["Subject"] = f"New Protocol Attestation by {name}"
            msg["From"] = "noreply@protocolattestation.app"
            msg["To"] = ", ".join(EMAIL_RECIPIENTS)
            body = f"""A supervisor has attested to the following CT protocol changes:

Name: {name}
Site: {site}
Timestamp: {timestamp}

Protocols:
{chr(10).join(active_protocols)}

This was logged in the system automatically."""
            msg.set_content(body)

            # Replace with your SMTP settings if needed
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login("your_email@gmail.com", "your_app_password")
                server.send_message(msg)
        except Exception as e:
            st.warning(f"Attestation saved, but email failed to send: {e}")
        else:
            st.success("✅ Your attestation has been recorded and email sent.")
