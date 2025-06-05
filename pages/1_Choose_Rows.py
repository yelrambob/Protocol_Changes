import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Choose Rows and Columns", layout="wide")

EXCEL_FILE = "protocol_sections.xlsx"
OUTPUT_FILE = "protocol_row_col_map.csv"

st.title("📝 Choose Rows and Columns")

if not os.path.exists(EXCEL_FILE):
    st.error("Excel file not found.")
    st.stop()

try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()

sheet_names = xl.sheet_names
selected_protocols = st.multiselect("Select protocol sheets to modify:", sheet_names)

rowcol_map = []

for protocol in selected_protocols:
    st.markdown(f"---\n### {protocol}")
    df = xl.parse(protocol)

    if df.empty:
        st.warning(f"{protocol} is empty.")
        continue

    default_rows = list(df.index[-3:])  # last 3 rows
    selected_rows = st.multiselect(f"Rows to include for {protocol}:", df.index.tolist(), default=default_rows, key=f"rows_{protocol}")

    selected_columns = st.multiselect(f"Columns to include for {protocol}:", df.columns.tolist(), default=list(df.columns), key=f"cols_{protocol}")

    col_renames = {}
    for col in selected_columns:
        new_name = st.text_input(f"Rename '{col}' in {protocol}:", value=col, key=f"rename_{protocol}_{col}")
        col_renames[col] = new_name

    description = st.text_area(f"Optional description of changes for {protocol}:", key=f"desc_{protocol}")

    for row in selected_rows:
        for col in selected_columns:
            rowcol_map.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenamedColumn": col_renames[col],
                "Description": description
            })

if st.button("💾 Save Changes"):
    df_output = pd.DataFrame(rowcol_map)
    df_output.to_csv(OUTPUT_FILE, index=False)
    st.success("Changes saved.")
