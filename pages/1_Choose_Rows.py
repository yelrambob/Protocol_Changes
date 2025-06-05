import streamlit as st
import pandas as pd
import os
from collections import Counter

# Streamlit page config
st.set_page_config(page_title="📋 Choose Rows and Columns", layout="wide")
st.title("📋 Choose Rows and Columns")

# File paths
EXCEL_FILE = "protocol_sections.xlsx"
SELECTION_FILE = "protocol_row_col_map.csv"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"

# File checks
if not os.path.exists(EXCEL_FILE):
    st.error("Excel file not found.")
    st.stop()
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please select protocols on the home page first.")
    st.stop()

# Load files
active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()
xl = pd.ExcelFile(EXCEL_FILE)

# Accumulate selections
all_selections = []
descriptions = {}

# UI loop
for protocol in active_protocols:
    st.markdown(f"---\n### {protocol}")
    df = xl.parse(protocol)

    # Select row for header renaming
    rename_row = st.number_input(
        f"Use this row to rename columns for {protocol}",
        min_value=0,
        max_value=len(df) - 1,
        value=0,
        step=1,
        key=f"rename_row_{protocol}"
    )

    # Rename columns using values from the selected row
    raw_headers = df.iloc[rename_row].astype(str).tolist()
    name_counter = Counter()
    new_headers = []
    for h in raw_headers:
        name_counter[h] += 1
        new_headers.append(f"{h}_{name_counter[h]}" if name_counter[h] > 1 else h)

    df.columns = new_headers
    df = df.iloc[rename_row + 1:].reset_index(drop=True)

    # Preview updated table
    st.dataframe(df, use_container_width=True)

    # Row and column selection
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

    # Optional description
    description = st.text_area(f"Optional: Description of changes for {protocol}", key=f"desc_{protocol}")
    descriptions[protocol] = description

    # Save selections
    for row in selected_rows:
        for col in selected_columns:
            all_selections.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenamedColumn": col,
                "Description": description,
                "RenameRow": rename_row
            })

# Save to file
if st.button("💾 Save Selections"):
    selection_df = pd.DataFrame(all_selections)
    selection_df.to_csv(SELECTION_FILE, index=False)
    st.success("Selections saved successfully.")
