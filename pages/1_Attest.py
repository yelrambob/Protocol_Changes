import streamlit as st
import pandas as pd
from datetime import datetime

ATTEST_LOG = "attestations.csv"
EXCEL_FILE = "AMG CT Protocols.xlsm"

# ✅ Use updated query param method
query_params = st.query_params
protocol = query_params.get("protocol", "")

st.title("✅ Protocol Attestation")

if not protocol:
    st.warning("No protocol specified in the URL. Use ?protocol=Your_Protocol")
    st.stop()

# Try to load Excel and find matching sheet
try:
    xl = pd.ExcelFile(EXCEL_FILE)
    if protocol not in xl.sheet_names:
        st.error(f"'{protocol}' not found in {EXCEL_FILE}. Available sheets: {', '.join(xl.sheet_names)}")
        st.stop()
    df = xl.parse(protocol)
except FileNotFoundError:
    st.error(f"Excel file '{EXCEL_FILE}' not found.")
    st.stop()
except Exception as e:
    st.error(f"Error reading '{EXCEL_FILE}': {e}")
    st.stop()

st.header(f"Review Section: {protocol}")
st.markdown("Below is the relevant protocol section:")

# Show the sheet content (read-only)
st.dataframe(df, use_container_width=True)

st.markdown("---")
st.subheader("🖊 Attestation Form")

name = st.text_input("Your Name")
site = st.text_input("Your Site")
confirm = st.checkbox("I attest that I have reviewed and will follow this protocol.")

if st.button("Submit Attestation"):
    if not name or not site or not confirm:
        st.warning("Please complete all fields and confirm.")
    else:
        new_entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Protocol": protocol,
            "Name": name,
            "Site": site
        }

        try:
            df_attest = pd.read_csv(ATTEST_LOG)
            df_attest = pd.concat([df_attest, pd.DataFrame([new_entry])], ignore_index=True)
        except FileNotFoundError:
            df_attest = pd.DataFrame([new_entry])

        df_attest.to_csv(ATTEST_LOG, index=False)
        st.success("✅ Your attestation has been recorded.")
