import streamlit as st
import pandas as pd
import os
import urllib.parse

EXCEL_FILE = "protocol_sections.xlsx"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
BASE_ATTEST_URL = "https://protocolchanges.streamlit.app/Attest?protocol="  # Update to match your app URL

st.set_page_config(page_title="CT Protocol Attestations", layout="wide")
st.title("📋 CT Protocol Attestation Center")

# --- Admin section to choose changed sheets ---
st.sidebar.header("Admin Controls")
st.sidebar.markdown("Select which protocols have been updated.")

try:
    xl = pd.ExcelFile(EXCEL_FILE)
    sheet_names = xl.sheet_names
except FileNotFoundError:
    st.error(f"Excel file '{EXCEL_FILE}' not found.")
    st.stop()

# Load previously selected protocols if available
if os.path.exists(ACTIVE_PROTOCOLS_FILE):
    saved = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
    default_selection = saved["Protocol"].tolist()
else:
    default_selection = []

selected_protocols = st.sidebar.multiselect("Select Changed Protocols", sheet_names, default=default_selection)

# Save active protocols list
if st.sidebar.button("✅ Save Active Protocols"):
    pd.DataFrame({"Protocol": selected_protocols}).to_csv(ACTIVE_PROTOCOLS_FILE, index=False)
    st.sidebar.success("Saved. The homepage will now show links for selected protocols.")

# --- Main homepage: Show available protocols ---
st.markdown("### 🔽 Protocols Available for Review & Attestation")

if not selected_protocols:
    st.info("No protocols currently selected. Use the sidebar to select them.")
else:
    for proto in selected_protocols:
        encoded = urllib.parse.quote(proto)
        attest_link = f"{BASE_ATTEST_URL}{encoded}"
        #st.markdown(f"- [**{proto}** → Attest here]({attest_link})")

