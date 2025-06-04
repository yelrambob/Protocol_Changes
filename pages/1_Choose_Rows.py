import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Choose Rows", layout="wide", initial_sidebar_state="collapsed")

EXCEL_FILE = "protocol_sections.xlsx"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
ROW_SELECTION_FILE = "protocol_row_map.csv"

st.title("📝 Choose Rows for Attestation")
st.markdown("Select which rows to display per protocol on the attestation page.")

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

row_selections = {}

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

    # Build index and label mapping
    index_list = list(df.index)
    label_map = {i: f"Row {i+1}" for i in index_list}
    reverse_map = {v: k for k, v in label_map.items()}

    # Default: last 3 rows + row 1 if present
    default_raw = [0] + list(df.index[-3:])
    default_indices = sorted(set(i for i in default_raw if i in df.index))
    default_labels = [label_map[i] for i in default_indices]

    selected_labels = st.multiselect(
        f"Select rows for {protocol}",
        options=[label_map[i] for i in df.index],
        default=default_labels,
        key=f"rows_{protocol}"
    )

    # Convert labels back to indices
    selected_indices = [reverse_map[label] for label in selected_labels]
    row_selections[protocol] = selected_indices

# Save to CSV
if st.button("💾 Save Row Selections"):
    all_rows = []
    for protocol, indices in row_selections.items():
        for idx in indices:
            all_rows.append({"Protocol": protocol, "RowIndex": idx})  # Store as 0-based index

    df_out = pd.DataFrame(all_rows)
    df_out.to_csv(ROW_SELECTION_FILE, index=False)
    st.success("Row selections saved successfully.")
