import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Choose Rows & Columns", layout="wide", initial_sidebar_state="collapsed")

EXCEL_FILE = "protocol_sections.xlsx"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ROW_SELECTION_FILE = "protocol_row_map.csv"
COL_SELECTION_FILE = "protocol_column_map.csv"

st.title("📝 Choose Rows and Columns for Attestation")
st.markdown("Select which rows and columns to display per protocol on the attestation page.")

# Load selected protocols
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please go to the Home page to select protocols first.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()

# Load the Excel file
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except FileNotFoundError:
    st.error(f"Excel file '{EXCEL_FILE}' not found.")
    st.stop()

row_selections = {}
col_selections = {}

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")
    if protocol not in xl.sheet_names:
        st.warning(f"'{protocol}' not found in the Excel file.")
        continue

    df = xl.parse(protocol)
    if df.empty:
        st.info("No data in this sheet.")
        continue

    st.dataframe(df, use_container_width=True)

    # ROW SELECTION

    index_list = list(df.index)
    label_map = {i: f"Row {i+1}" for i in index_list}
    reverse_map = {v: k for k, v in label_map.items()}

    # Default: last 3 + first row (or all if you want — change next line to list(df.index))
    default_raw = [0] + list(df.index[-3:]) # uncomment here and recomment the line below to change it to all rows 
    #default_raw = list(df.index)  # Select all rows 
    default_indices = sorted(set(i for i in default_raw if i in df.index))
    default_labels = [label_map[i] for i in default_indices]

    select_all_rows = st.checkbox(f"Select all rows for {protocol}", key=f"all_rows_{protocol}")
    selected_labels = st.multiselect(
        f"Select rows for {protocol}",
        options=[label_map[i] for i in df.index],
        default=[label_map[i] for i in df.index] if select_all_rows else default_labels,
        key=f"rows_{protocol}"
    )
    selected_indices = [reverse_map[label] for label in selected_labels]
    row_selections[protocol] = selected_indices

    # COLUMN SELECTION

    col_list = list(df.columns)
    select_all_cols = st.checkbox(f"Select all columns for {protocol}", key=f"all_cols_{protocol}")
    selected_cols = st.multiselect(
        f"Select columns for {protocol}",
        options=col_list,
        default=col_list if select_all_cols else col_list,  # ← Change this if you want partial default
        key=f"cols_{protocol}"
    )
    col_selections[protocol] = selected_cols

# SAVE
if st.button("💾 Save Selections"):
    row_data = []
    for protocol, indices in row_selections.items():
        for idx in indices:
            row_data.append({"Protocol": protocol, "RowIndex": idx})

    col_data = []
    for protocol, cols in col_selections.items():
        for col in cols:
            col_data.append({"Protocol": protocol, "ColumnName": col})

    pd.DataFrame(row_data).to_csv(ROW_SELECTION_FILE, index=False)
    pd.DataFrame(col_data).to_csv(COL_SELECTION_FILE, index=False)

    st.success("Row and column selections saved successfully.")
