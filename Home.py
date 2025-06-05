import streamlit as st
import pandas as pd
import urllib.parse
import storage  # Supabase-based data handler
from Streamlit_App_Rewrite import EXCEL_FILE  # used for reading local Excel sheet

BASE_ATTEST_URL = "https://protocolchanges.streamlit.app/Attest?protocol="

st.set_page_config(page_title="CT Protocol Attestations", layout="wide")
st.title("📋 CT Protocol Attestation Center")

# --- Admin sidebar to choose changed sheets ---
st.sidebar.header("Admin Controls")
st.sidebar.markdown("Select which protocols have been updated.")

# Load available sheet names
try:
    xl = pd.ExcelFile(EXCEL_FILE)
    sheet_names = xl.sheet_names
except FileNotFoundError:
    st.error(f"Excel file '{EXCEL_FILE}' not found.")
    st.stop()

# Load saved protocols from Supabase
try:
    saved_df = storage.get_active_protocols()
    default_selection = saved_df["protocol"].tolist() if not saved_df.empty else []
except Exception as e:
    st.error(f"Could not load active protocols: {e}")
    default_selection = []

# Allow selection of protocols
selected_protocols = st.sidebar.multiselect(
    "Select Changed Protocols", sheet_names, default=default_selection
)

# Save button
if st.sidebar.button("✅ Save Active Protocols"):
    try:
        storage.set_active_protocols(selected_protocols)
        st.sidebar.success("Saved to Supabase. The homepage will now show links.")
    except Exception as e:
        st.sidebar.error(f"Error saving: {e}")

# Clear row/column selections button
if st.sidebar.button("🗑️ Clear Saved Row/Column Settings for Selected Protocols"):
    if selected_protocols:
        try:
            storage.clear_row_col_map_for(selected_protocols)
            st.sidebar.success("Row/column settings cleared for selected protocols.")
        except Exception as e:
            st.sidebar.error(f"Error clearing selections: {e}")
    else:
        st.sidebar.info("No protocols selected to clear.")

# --- Show protocol links for attestation ---
st.markdown("### 🔽 Protocols Available for Review & Attestation")

if not selected_protocols:
    st.info("No protocols currently selected. Use the sidebar to select them.")
else:
    for proto in selected_protocols:
        encoded = urllib.parse.quote(proto)
        attest_link = f"{BASE_ATTEST_URL}{encoded}"
        st.markdown(f"- [**{proto}** → Attest here]({attest_link})")
