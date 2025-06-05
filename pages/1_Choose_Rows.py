import streamlit as st
import pandas as pd
import os

EXCEL_FILE = "protocol_sections.xlsx"
ROWCOL_SELECTION_FILE = "protocol_row_col_map.csv"
ACTIVE_PROTOCOLS_FILE = "active_protocols.csv"
LOCK_FILE = "locked.flag"

st.set_page_config(
    page_title="Choose Rows and Columns",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧩 Choose Rows and Columns")

# Lock system
if os.path.exists(LOCK_FILE):
    st.warning("⚠️ Protocol selections are locked. Unlock below to make changes.")
    password = st.text_input("Enter password to unlock:", type="password")
    if password == "123":  # Replace with your password
        os.remove(LOCK_FILE)
        st.success("Unlocked. You may now make changes.")
        st.experimental_rerun()
    else:
        st.stop()
else:
    if st.button("🔒 Lock selections (password required to unlock)"):
        open(LOCK_FILE, "w").close()
        st.success("Selections locked.")
        st.experimental_rerun()

# Load active protocols
if not os.path.exists(ACTIVE_PROTOCOLS_FILE):
    st.warning("Please select protocols on the Home page first.")
    st.stop()

active_df = pd.read_csv(ACTIVE_PROTOCOLS_FILE)
active_protocols = active_df["Protocol"].tolist()

try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

rowcol_data = []

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")
    try:
        df = xl.parse(protocol)
    except Exception as e:
        st.error(f"Failed to load sheet for {protocol}: {e}")
        continue

    st.dataframe(df, use_container_width=True)

    # Select rename row (to extract headers from)
    rename_row = st.number_input(
        f"Select the row number to rename columns for {protocol}:",
        min_value=0, max_value=len(df)-1, value=0, step=1, key=f"rename_{protocol}"
    )

    # Get renamed columns
    new_headers = df.iloc[int(rename_row)].astype(str).tolist()
    df.columns = new_headers
    df = df.iloc[int(rename_row) + 1:].reset_index(drop=True)

    # Select rows and columns
    selected_rows = st.multiselect(
        f"Select rows for {protocol}", options=list(df.index), default=list(df.index), key=f"rows_{protocol}"
    )
    selected_cols = st.multiselect(
        f"Select columns for {protocol}", options=list(df.columns), default=list(df.columns), key=f"cols_{protocol}"
    )

    # Optional notes for this protocol
    notes = st.text_area(f"Optional notes for {protocol}", key=f"notes_{protocol}")

    for row in selected_rows:
        for col in selected_cols:
            rowcol_data.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenameRow": rename_row,
                "Description": notes
            })

# Save
if st.button("💾 Save Selections"):
    if rowcol_data:
        df_out = pd.DataFrame(rowcol_data)
        df_out.to_csv(ROWCOL_SELECTION_FILE, index=False)
        st.success("Selections saved successfully.")
    else:
        st.warning("No data to save.")
