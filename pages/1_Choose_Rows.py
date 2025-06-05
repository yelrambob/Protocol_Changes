import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Choose Rows and Columns",
    layout="wide",
    initial_sidebar_state="auto"
)

st.title("🔧 Choose Rows, Columns, and Describe Changes")

EXCEL_FILE = "protocol_sections.xlsx"
ROWCOL_SELECTION_FILE = "protocol_row_col_map.csv"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"

if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please select protocols on the home page first.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
protocols = active_df["Protocol"].tolist()

try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

rowcol_entries = []

for protocol in protocols:
    st.markdown(f"---\n### 📄 {protocol}")

    df = xl.parse(protocol)
    if df.empty:
        st.warning(f"No data found in {protocol} sheet.")
        continue

    st.dataframe(df)

    row_indices = st.multiselect(
        f"Select rows for {protocol}", options=list(df.index), default=list(df.index[-20:]), key=f"rows_{protocol}"
    )

    columns = st.multiselect(
        f"Select columns for {protocol}", options=list(df.columns), default=[df.columns[i] for i in [1, 3, 4, 7, 9, 10, 12, 14] if i < len(df.columns)], key=f"cols_{protocol}"
    )

    rename_dict = {}
    for col in columns:
        new_name = st.text_input(f"Rename '{col}' in {protocol} (optional)", value=col, key=f"rename_{protocol}_{col}")
        rename_dict[col] = new_name

    description = st.text_area(f"Describe the protocol change for {protocol}", key=f"desc_{protocol}")

    for row in row_indices:
        for col in columns:
            rowcol_entries.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenamedColumn": rename_dict[col],
                "Description": description
            })

if st.button("💾 Save Changes"):
    df_all = pd.DataFrame(rowcol_entries)
    df_all.to_csv(ROWCOL_SELECTION_FILE, index=False)
    st.success("Changes saved successfully.")
