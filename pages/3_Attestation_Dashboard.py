import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime

ATTEST_LOG = "attestation_log.csv"

st.set_page_config(
    page_title="Attestation Dashboard",
    layout="wide"
)

st.title("📊 Attestation Dashboard")

if not os.path.exists(ATTEST_LOG):
    st.warning("No attestation records found yet.")
    st.stop()

# Load data
log_df = pd.read_csv(ATTEST_LOG)
log_df.reset_index(inplace=True)  # Add row numbers as index column
log_df.rename(columns={"index": "Row Number"}, inplace=True)

# Keep only necessary columns
columns_to_keep = ["Row Number", "Site", "Name", "Timestamp", "Protocols Completed"]
columns_in_log = log_df.columns.tolist()
additional_columns = [col for col in columns_in_log if col not in columns_to_keep and col != "Protocols Reviewed"]
filtered_display_df = log_df[columns_to_keep + additional_columns]

# Search and filter controls
with st.expander("🔍 Filter Options", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_site = st.multiselect("Filter by site:", options=filtered_display_df["Site"].dropna().unique())
    with col2:
        selected_name = st.multiselect("Filter by name:", options=filtered_display_df["Name"].dropna().unique())
    with col3:
        date_range = st.date_input("Filter by date range:", [])

    filtered_df = filtered_display_df.copy()
    if selected_site:
        filtered_df = filtered_df[filtered_df["Site"].isin(selected_site)]
    if selected_name:
        filtered_df = filtered_df[filtered_df["Name"].isin(selected_name)]
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df["Timestamp"], errors='coerce') >= pd.to_datetime(start_date)
        ]
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df["Timestamp"], errors='coerce') <= pd.to_datetime(end_date)
        ]

# Display table
st.dataframe(filtered_df, use_container_width=True)

# Export
with st.expander("📁 Export", expanded=False):
    export_btn = st.button("Export filtered data to Excel")
    if export_btn:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Attestations")
        st.download_button(
            label="Download Excel File",
            data=buffer.getvalue(),
            file_name="attestation_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Delete functionality
with st.expander("🗑️ Delete Entries", expanded=False):
    if not filtered_df.empty:
        selected_to_delete = st.multiselect(
            "Select row numbers to delete:",
            options=filtered_df["Row Number"].tolist()
        )
        if st.button("Delete Selected"):
            updated_df = log_df[~log_df["Row Number"].isin(selected_to_delete)]
            updated_df.drop(columns=["Row Number"], inplace=True, errors='ignore')
            updated_df.to_csv(ATTEST_LOG, index=False)
            st.success("Selected entries deleted. Please refresh the page.")
    else:
        st.info("No entries available for deletion.")
