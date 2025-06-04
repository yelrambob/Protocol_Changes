import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

ATTEST_LOG = "attestations.csv"
PAGE_MAP_FILE = "protocol_pages.csv"

# Get ?protocol= parameter
query_params = st.experimental_get_query_params()
protocol = query_params.get("protocol", [""])[0].replace("_", " ")

st.title("✅ Protocol Attestation")

if not protocol:
    st.warning("No protocol specified in the URL. Use ?protocol=Your_Protocol")
    st.stop()

# Load PDF page mapping
try:
    page_df = pd.read_csv(PAGE_MAP_FILE)
    match = page_df[page_df["Protocol"] == protocol]
    if match.empty:
        st.error("Protocol not found in page mapping.")
        st.stop()
    else:
        pdf_url = match["PDF_URL"].iloc[0]
        start_page = match["StartPage"].iloc[0]
except Exception as e:
    st.error(f"Error loading PDF mapping: {e}")
    st.stop()

st.header(f"Review Protocol: {protocol}")

# Generate viewer URL
viewer = "https://mozilla.github.io/pdf.js/web/viewer.html"
embed_url = f"{viewer}?file={urllib.parse.quote(pdf_url)}#page={start_page}"

# Display embedded viewer
st.components.v1.iframe(embed_url, height=700, scrolling=True)

st.markdown("---")
st.subheader("Attestation Form")

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
            df = pd.read_csv(ATTEST_LOG)
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([new_entry])

        df.to_csv(ATTEST_LOG, index=False)
        st.success("✅ Your attestation has been recorded.")
