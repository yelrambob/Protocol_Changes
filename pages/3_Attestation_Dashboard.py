import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Protocol Changes", layout="wide", initial_sidebar_state="collapsed")

if os.path.exists(CHANGE_LOG) and os.path.getsize(CHANGE_LOG) > 0:
    change_df = pd.read_csv(CHANGE_LOG)
else:
    st.warning("No protocol change log found or it's empty.")
    st.stop()

CHANGE_LOG = "protocol_change_log.csv"
ATTEST_LOG = "attestations.csv"

st.title("📋 Protocol Attestation Dashboard")

if not os.path.exists(CHANGE_LOG):
    st.warning("No protocol changes found.")
    st.stop()

change_df = pd.read_csv(CHANGE_LOG)
attest_df = pd.read_csv(ATTEST_LOG) if os.path.exists(ATTEST_LOG) else pd.DataFrame(columns=["Protocol", "Name", "Site", "Timestamp"])

st.subheader("✅ Summary of Attestations")

# Protocols list
protocols = sorted(change_df["Protocol"].unique())

for protocol in protocols:
    st.markdown(f"### 🧪 {protocol}")

    # Who was notified?
    recipients = change_df[change_df["Protocol"] == protocol]["Recipients"].iloc[-1]
    recipients_list = [email.strip() for email in recipients.split(",")]

    # Who attested?
    attest_names = attest_df[attest_df["Protocol"] == protocol]["Name"].unique().tolist()

    st.write(f"- Notified: {', '.join(recipients_list)}")
    st.write(f"- Attested: {', '.join(attest_names) if attest_names else 'None yet'}")

    # Missing attestations
    missing = [r for r in recipients_list if r.split("@")[0] not in [a.split()[0].lower() for a in attest_names]]
    if missing:
        st.warning(f"⚠️ Awaiting attestations from: {', '.join(missing)}")
    else:
        st.success("✅ All recipients have attested.")
