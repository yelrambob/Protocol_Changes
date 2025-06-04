# ✅ File: pages/3_Choose_Rows.py

import streamlit as st
import pandas as pd
import os

EXCEL_FILE = "protocol_sections.xlsx"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ROW_SELECTION_FILE = "protocol_row_map.csv"

st.set_page_config(page_title="Protocol Changes", layout="wide", initial_sidebar_state="collapsed")
st.title("🧩 Select Rows to Include per Protocol")

# Load active protocols
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("No active protocols selected. Please go to Home and choose protocols first.")
    st.stop()

try:
    protocol_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
    active_protocols = protocol_df["Protocol"].tolist()
except Exception as e:
    st.error(f"Error reading active protocols: {e}")
    st.stop()

# Load Excel
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except FileNotFoundError:
    st.error(f"Excel file '{EXCEL_FILE}' not found.")
    st.stop()

selected_rows = []

st.markdown("### Select which rows to include for each protocol:")

for protocol in active_protocols:
    if protocol not in xl.sheet_names:
        st.warning(f"'{protocol}' not found in Excel file.")
        continue

    st.markdown(f"---\n#### {protocol}")
    try:
        df = xl.parse(protocol)
        df_display = df.copy()
        df_display.index = df_display.index + 1  # Show row index starting at 1
        selected = st.multiselect(
            f"Select rows for {protocol}",
            options=list(df_display.index),
            default=list(df_display.index),
            key=f"rows_{protocol}"
        )

        for row_index in selected:
            selected_rows.append({"Protocol": protocol, "RowIndex": row_index})

        st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.warning(f"Error displaying {protocol}: {e}")

if st.button("💾 Save Row Selections"):
    pd.DataFrame(selected_rows).to_csv(ROW_SELECTION_FILE, index=False)
    st.success("Selected rows saved successfully!")
