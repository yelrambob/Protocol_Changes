import streamlit as st
import pandas as pd
import os

title = "📋 Choose Rows and Columns"
st.set_page_config(page_title=title, layout="wide")
st.title(title)

EXCEL_FILE = "protocol_sections.xlsx"
SELECTION_FILE = "protocol_row_col_map.csv"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"

if not os.path.exists(EXCEL_FILE):
    st.error("Excel file not found.")
    st.stop()
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please select protocols on the home page first.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()

xl = pd.ExcelFile(EXCEL_FILE)

all_selections = []

descriptions = {}

for protocol in active_protocols:
    st.markdown(f"---\n### {protocol}")
    df = xl.parse(protocol)

    # Let user optionally rename columns from a selected row
    rename_row = st.number_input(
        f"Optional: Pick a row number to rename columns for {protocol}",
        min_value=0,
        max_value=len(df) - 1,
        value=0,
        step=1,
        key=f"row_input_{protocol}"
    )

    if st.button(f"Use row {rename_row} as header for {protocol}", key=f"use_row_{protocol}"):
        new_names = df.iloc[rename_row].astype(str).tolist()
        df.columns = new_names
        df = df.iloc[rename_row + 1:].reset_index(drop=True)
        st.success(f"Renamed columns for {protocol} using row {rename_row}")

    selected_rows = st.multiselect(
        f"Select rows for {protocol}",
        options=list(df.index),
        default=list(df.index[-3:]),
        key=f"rows_{protocol}"
    )

    selected_columns = st.multiselect(
        f"Select columns for {protocol}",
        options=list(df.columns),
        default=list(df.columns),
        key=f"cols_{protocol}"
    )

    # Let user rename columns
    col_renames = {}
    st.markdown("#### Rename Selected Columns")
    for col in selected_columns:
        new_name = st.text_input(f"Rename column '{col}'", value=col, key=f"rename_{protocol}_{col}")
        col_renames[col] = new_name

    # Add description
    description = st.text_area(f"Optional: Description of changes for {protocol}", key=f"desc_{protocol}")
    descriptions[protocol] = description

    for row in selected_rows:
        for col in selected_columns:
            all_selections.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenamedColumn": col_renames[col],
                "Description": description
            })

if st.button("💾 Save Selections"):
    selection_df = pd.DataFrame(all_selections)
    selection_df.to_csv(SELECTION_FILE, index=False)
    st.success("Selections saved successfully.")
