import streamlit as st
import pandas as pd
import os
import csv

# Set up directory for persistent storage
BASE_DIR = "data"
os.makedirs(BASE_DIR, exist_ok=True)

EXCEL_FILE = "protocol_sections.xlsx"
ROWCOL_SELECTION_FILE = os.path.join(BASE_DIR, "protocol_row_col_map.csv")
ACTIVE_PROTOCOLS_FILE = os.path.join(BASE_DIR, "active_protocols.csv")
LOCK_FILE = os.path.join(BASE_DIR, "locked.flag")

st.set_page_config(
    page_title="Choose Rows and Columns",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎩 Choose Rows and Columns")

if os.path.exists(LOCK_FILE):
    st.warning("⚠️ Protocol selections are locked. Unlock below to make changes.")
    password = st.text_input("Enter password to unlock:", type="password")
    if password == "changeme":
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

if not os.path.exists(ROWCOL_SELECTION_FILE) or os.path.getsize(ROWCOL_SELECTION_FILE) == 0:
    saved_df = pd.DataFrame(columns=["Protocol", "RowIndex", "OriginalColumn", "RenameRow", "Description"])
    st.warning("⚠️ No saved selections found or file is empty. Starting fresh.")
else:
    try:
        with open(ROWCOL_SELECTION_FILE, "r") as f:
            has_header = csv.Sniffer().has_header(f.read(1024))
            f.seek(0)
        if has_header:
            saved_df = pd.read_csv(ROWCOL_SELECTION_FILE)
        else:
            saved_df = pd.DataFrame(columns=["Protocol", "RowIndex", "OriginalColumn", "RenameRow", "Description"])
            st.warning("⚠️ CSV has no header row. Starting fresh.")
    except Exception as e:
        st.error(f"Failed to read saved selections: {e}")
        saved_df = pd.DataFrame(columns=["Protocol", "RowIndex", "OriginalColumn", "RenameRow", "Description"])

rowcol_data = []

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")
    try:
        df = xl.parse(protocol)
    except Exception as e:
        st.error(f"Failed to load sheet for {protocol}: {e}")
        continue

    st.dataframe(df, use_container_width=True)

    saved_protocol = saved_df[saved_df["Protocol"] == protocol]

    default_rename_row = int(saved_protocol["RenameRow"].iloc[0]) if not saved_protocol.empty else 0
    rename_row = st.number_input(
        f"Select the row number to rename columns for {protocol}:",
        min_value=0, max_value=len(df)-1, value=default_rename_row, step=1, key=f"rename_{protocol}"
    )

    new_headers = df.iloc[int(rename_row)].astype(str).tolist()
    df.columns = new_headers
    df = df.iloc[int(rename_row) + 1:].reset_index(drop=True)

    default_rows = saved_protocol["RowIndex"].dropna().astype(int).unique().tolist()
    default_cols = saved_protocol["OriginalColumn"].dropna().unique().tolist()

    safe_default_rows = [r for r in default_rows if r in df.index]
    safe_default_cols = [c for c in default_cols if c in df.columns]

    selected_rows = st.multiselect(
        f"Select rows for {protocol}", options=list(df.index), default=safe_default_rows or list(df.index), key=f"rows_{protocol}"
    )
    selected_cols = st.multiselect(
        f"Select columns for {protocol}", options=list(df.columns), default=safe_default_cols or list(df.columns), key=f"cols_{protocol}"
    )

    default_note = saved_protocol["Description"].iloc[0] if not saved_protocol.empty else ""
    notes = st.text_area(f"Optional notes for {protocol}", value=default_note, key=f"notes_{protocol}")

    for row in selected_rows:
        for col in selected_cols:
            rowcol_data.append({
                "Protocol": protocol,
                "RowIndex": row,
                "OriginalColumn": col,
                "RenameRow": rename_row,
                "Description": notes
            })

if st.button("📊 Save Selections"):
    if rowcol_data:
        df_out = pd.DataFrame(rowcol_data)
        if not df_out.empty:
            df_out.to_csv(ROWCOL_SELECTION_FILE, index=False)
            st.success("Selections saved successfully.")
        else:
            st.warning("Nothing to save — the table is empty.")
    else:
        st.warning("No data to save.")
