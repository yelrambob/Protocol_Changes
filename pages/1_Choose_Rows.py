import streamlit as st
import pandas as pd
import os
import storage
from Streamlit_App_Rewrite import EXCEL_FILE, LOCK_FILE

st.set_page_config(
    page_title="Choose Rows and Columns",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎩 Choose Rows and Columns")

# Lock/unlock system
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

# Load active protocols from Supabase
active_df = storage.get_active_protocols()
if active_df.empty:
    st.warning("Please select protocols on the Home page first.")
    st.stop()

active_protocols = active_df["protocol"].dropna().tolist()

# Load Excel file
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

# Load saved row/col map
saved_df = storage.get_row_col_map()

rowcol_data = []

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")
    try:
        df = xl.parse(protocol)
    except Exception as e:
        st.error(f"Failed to load sheet for {protocol}: {e}")
        continue

    st.dataframe(df, use_container_width=True)

    saved_protocol = saved_df[saved_df["protocol"] == protocol]

    default_rename_row = int(saved_protocol["rename_row"].iloc[0]) if not saved_protocol.empty else 0
    rename_row = st.number_input(
        f"Select the row number to rename columns for {protocol}:",
        min_value=0, max_value=len(df)-1, value=default_rename_row, step=1, key=f"rename_{protocol}"
    )

    new_headers = df.iloc[int(rename_row)].astype(str).tolist()
    df.columns = new_headers
    df = df.iloc[int(rename_row) + 1:].reset_index(drop=True)

    default_rows = saved_protocol["row_index"].dropna().astype(int).unique().tolist()
    default_cols = saved_protocol["original_column"].dropna().unique().tolist()

    safe_default_rows = [r for r in default_rows if r in df.index]
    safe_default_cols = [c for c in default_cols if c in df.columns]

    selected_rows = st.multiselect(
        f"Select rows for {protocol}", options=list(df.index),
        default=safe_default_rows or list(df.index), key=f"rows_{protocol}"
    )
    selected_cols = st.multiselect(
        f"Select columns for {protocol}", options=list(df.columns),
        default=safe_default_cols or list(df.columns), key=f"cols_{protocol}"
    )

    default_note = saved_protocol["description"].iloc[0] if not saved_protocol.empty else ""
    notes = st.text_area(f"Optional notes for {protocol}", value=default_note, key=f"notes_{protocol}")

    for row in selected_rows:
        for col in selected_cols:
            rowcol_data.append({
                "protocol": protocol,
                "row_index": row,
                "original_column": col,
                "rename_row": rename_row,
                "description": notes
            })

# Save all selections to Supabase
if st.button("📊 Save Selections"):
    if rowcol_data:
        df_out = pd.DataFrame(rowcol_data)
        try:
            storage.set_row_col_map(df_out)
            st.success("Selections saved to Supabase.")
        except Exception as e:
            st.error(f"Failed to save selections: {e}")
    else:
        st.warning("No data to save.")
