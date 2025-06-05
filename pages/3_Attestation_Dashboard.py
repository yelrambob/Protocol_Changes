import streamlit as st
import pandas as pd
import storage
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="Attestation Dashboard",
    layout="wide"
)

st.title("📊 Attestation Dashboard")

# Load attestation data from Supabase
try:
    log_df = storage.get_attestation_log()
except Exception as e:
    st.error(f"Failed to load attestation log: {e}")
    st.stop()

if log_df.empty:
    st.warning("No attestation records found yet.")
    st.stop()

log_df.reset_index(inplace=True)
log_df.rename(columns={"index": "Row Number"}, inplace=True)

# Define display columns
required = ["Row Number", "site", "name", "timestamp", "protocols_completed"]
available_required = [col for col in required if col in log_df.columns]
extra_columns = [col for col in log_df.columns if col not in available_required and col not in ["protocols_reviewed"]]
final_columns = available_required + extra_columns
filtered_display_df = log_df[final_columns]

# Filters
with st.expander("🔍 Filter Options", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_site = st.multiselect("Filter by site:", options=filtered_display_df["site"].dropna().unique()) if "site" in filtered_display_df.columns else []

    with col2:
        selected_name = st.multiselect("Filter by name:", options=filtered_display_df["name"].dropna().unique()) if "name" in filtered_display_df.columns else []

    with col3:
        date_range = st.date_input("Filter by date range:", []) if "timestamp" in filtered_display_df.columns else []

    filtered_df = filtered_display_df.copy()

    if selected_site:
        filtered_df = filtered_df[filtered_df["site"].isin(selected_site)]
    if selected_name:
        filtered_df = filtered_df[filtered_df["name"].isin(selected_name)]
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df["timestamp"], errors='coerce') >= pd.to_datetime(start_date)
        ]
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df["timestamp"], errors='coerce') <= pd.to_datetime(end_date)
        ]

# Display filtered log
st.dataframe(filtered_df, use_container_width=True)

# Export
with st.expander("📁 Export", expanded=False):
    if st.button("Export filtered data to Excel"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Attestations")
        st.download_button(
            label="Download Excel File",
            data=buffer.getvalue(),
            file_name=f"attestations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Delete
with st.expander("🗑️ Delete Entries", expanded=False):
    if not filtered_df.empty and "id" in log_df.columns:
        selected_to_delete = st.multiselect("Select row IDs to delete:", options=filtered_df["id"].tolist())
        if st.button("Delete Selected"):
            try:
                storage.delete_attestation_rows(selected_to_delete)
                st.success("Selected entries deleted. Please refresh the page.")
            except Exception as e:
                st.error(f"Error deleting rows: {e}")
    else:
        st.info("No entries available for deletion or missing ID column.")
