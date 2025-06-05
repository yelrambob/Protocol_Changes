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

rowcol_map = []

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")
    if protocol not in xl.sheet_names:
        st.warning(f"'{protocol}' not found in Excel.")
        continue

    df = xl.parse(protocol)
    if df.empty:
        st.info("No data in this sheet.")
        continue

    st.dataframe(df, use_container_width=True)

    # 📌 Description of changes
    description = st.text_area(f"📝 Describe changes for {protocol}", key=f"{protocol}_desc")

    # Default selections
    default_raw = [0] + list(df.index[-3:])
    default_indices = sorted(set(i for i in default_raw if i in df.index))
    label_map = {i: f"Row {i+1}" for i in df.index}
    reverse_map = {v: k for k, v in label_map.items()}

    select_all = st.checkbox(f"Select all rows for {protocol}", key=f"all_{protocol}")
    selected_labels = st.multiselect(
        f"Select rows for {protocol}",
        options=[label_map[i] for i in df.index],
        default=[label_map[i] for i in df.index] if select_all else [label_map[i] for i in default_indices],
        key=f"rows_{protocol}"
    )
    selected_indices = [reverse_map[label] for label in selected_labels]

    # Column selection + rename
    all_cols = list(df.columns)
    selected_cols = st.multiselect(f"Select columns to show for {protocol}", options=all_cols, default=all_cols)
    renamed_cols = {}
    for col in selected_cols:
        new_name = st.text_input(f"Rename '{col}'", value=col, key=f"{protocol}_{col}_rename")
        renamed_cols[col] = new_name

    # Append all mappings with description
    for row in selected_indices:
        for col in selected_cols:
            rowcol_map.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenamedColumn": renamed_cols[col],
                "Description": description.strip()
            })


# SAVE
if st.button("💾 Save Selections"):
    pd.DataFrame(selection_records).to_csv(ROWCOL_SELECTION_FILE, index=False)
    st.success("Row + column selections (with renames) saved to protocol_row_col_map.csv")
