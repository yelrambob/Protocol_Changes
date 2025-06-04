import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Choose Rows & Columns", layout="wide", initial_sidebar_state="collapsed")

EXCEL_FILE = "protocol_sections.xlsx"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ROWCOL_SELECTION_FILE = "protocol_row_col_map.csv"

st.title("📝 Choose Rows and Columns for Attestation")
st.markdown("Select which rows and columns to display per protocol. You can also rename columns as they’ll appear on the attestation page.")

# Load active protocols
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please go to the Home page to select protocols first.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()

# Load Excel workbook
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except FileNotFoundError:
    st.error(f"Excel file '{EXCEL_FILE}' not found.")
    st.stop()

selection_records = []

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

    # ROWS
    index_list = list(df.index)
    label_map = {i: f"Row {i+1}" for i in index_list}
    reverse_map = {v: k for k, v in label_map.items()}

    default_raw = [0] + list(df.index[-3:])  # ← Change to list(df.index) for all
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

    # COLUMNS + rename
    col_list = list(df.columns)
    select_all_cols = st.checkbox(f"Select all columns for {protocol}", key=f"all_cols_{protocol}")
    selected_cols = st.multiselect(
        f"Select columns for {protocol}",
        options=col_list,
        default=col_list if select_all_cols else col_list,
        key=f"cols_{protocol}"
    )

    renamed_cols = {}
    st.markdown("#### ✏️ Rename Selected Columns (Optional)")
    for col in selected_cols:
        new_name = st.text_input(f"Rename '{col}'", value=col, key=f"rename_{protocol}_{col}")
        renamed_cols[col] = new_name

    # Combine selections
    for row in selected_indices:
        for col in selected_cols:
            selection_records.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenamedColumn": renamed_cols.get(col, col)
            })

# SAVE
if st.button("💾 Save Selections"):
    pd.DataFrame(selection_records).to_csv(ROWCOL_SELECTION_FILE, index=False)
    st.success("Row + column selections (with renames) saved to protocol_row_col_map.csv")
