import streamlit as st
import pandas as pd
import os
from collections import Counter

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

    rename_row = st.number_input(
        f"Use this row to rename columns for {protocol}:",
        min_value=0,
        max_value=len(df) - 1,
        value=0,
        step=1,
        key=f"row_input_{protocol}"
    )
    new_names_raw = df.iloc[rename_row].astype(str).tolist()

    # Force uniqueness by appending suffix to duplicates
    name_counter = Counter()
    new_names = []
    for name in new_names_raw:
        name_counter[name] += 1
        new_name = f"{name}_{name_counter[name]}" if name_counter[name] > 1 else name
        new_names.append(new_name)

    df.columns = new_names
    df = df.iloc[rename_row + 1:].reset_index(drop=True)

    # Show full preview
    st.dataframe(df, use_container_width=True)

    selected_rows = st.multiselect(
        f"Select rows for {protocol}",
        options=list(df.index),
        default=list(df.index),
        key=f"rows_{protocol}"
    )

    selected_columns = st.multiselect(
        f"Select columns for {protocol}",
        options=list(df.columns),
        default=list(df.columns),
        key=f"cols_{protocol}"
    )

    description = st.text_area(f"Optional: Description of changes for {protocol}", key=f"desc_{protocol}")
    descriptions[protocol] = description

    for row in selected_rows:
        for col in selected_columns:
            all_selections.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenamedColumn": col,
                "Description": description
            })

if st.button("💾 Save Selections"):
    selection_df = pd.DataFrame(all_selections)
    selection_df.to_csv(SELECTION_FILE, index=False)
    st.success("Selections saved successfully.")
