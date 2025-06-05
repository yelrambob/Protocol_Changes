import streamlit as st
import pandas as pd
import storage
from Streamlit_App_Rewrite import EXCEL_FILE

st.set_page_config(page_title="Choose Rows and Columns", layout="wide")
st.title("🧩 Choose Rows and Columns for Protocols")

# Load active protocols
active_df = storage.get_active_protocols()
if active_df.empty or "protocol" not in active_df.columns:
    st.warning("Active protocols file missing. Please select protocols first.")
    st.stop()

active_protocols = active_df["protocol"].dropna().tolist()
if not active_protocols:
    st.info("No protocols selected.")
    st.stop()

# Load workbook
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()

rowcol_data = []

st.markdown("This tool lets you choose which rows and columns to save for each protocol.")

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")

    try:
        df = xl.parse(protocol)
    except Exception as e:
        st.warning(f"Error reading sheet '{protocol}': {e}")
        continue

    if df.empty:
        st.warning("This sheet is empty.")
        continue

    rename_row = st.number_input(
        f"Row to rename columns (0-indexed):", min_value=0, max_value=len(df)-1,
        value=0, key=f"rename_{protocol}"
    )

    raw_headers = df.iloc[rename_row].astype(str).tolist()
    df.columns = raw_headers
    df = df.iloc[rename_row + 1:].reset_index(drop=True)

    selected_cols = st.multiselect(
        f"Select columns for {protocol}", options=list(df.columns),
        default=list(df.columns[:3]), key=f"cols_{protocol}"
    )

    selected_rows = st.multiselect(
        f"Select rows for {protocol} (by index):", options=list(df.index[:20]),
        default=list(df.index[:3]), key=f"rows_{protocol}"
    )

    description = st.text_area(f"Optional notes for {protocol}:", key=f"desc_{protocol}")

    if not selected_cols or not selected_rows:
        st.info(f"⚠️ No data selected for {protocol}. This will not be saved.")
        continue

    for row in selected_rows:
        for col in selected_cols:
            rowcol_data.append({
                "protocol": protocol,
                "row_index": row,
                "original_column": col,
                "rename_row": rename_row,
                "description": description
            })

# Save selections (ensure Streamlit captures final state)
if st.button("📊 Save Selections"):
    st.session_state.update()

    if rowcol_data:
        df_out = pd.DataFrame(rowcol_data)
        df_out = df_out[df_out["row_index"].notna() & df_out["original_column"].notna()]
        df_out = df_out.sort_values(by=["protocol", "row_index", "original_column"])

        try:
            storage.set_row_col_map(df_out)
            st.success("Selections saved to Supabase.")
        except Exception as e:
            st.error(f"Failed to save selections: {e}")
    else:
        st.warning("Nothing selected to save. Please make sure at least one row and column are picked.")
