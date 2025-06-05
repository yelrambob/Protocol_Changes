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

# Load Excel workbook
try:
    xl = pd.ExcelFile(EXCEL_FILE)
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()

# Load existing row/column selections
existing_df = storage.get_row_col_map()
existing_df.columns = [c.lower() for c in existing_df.columns]

rowcol_data = []
st.markdown("Use this tool to configure which rows and columns will be saved for each protocol. Your selections will appear in the attest page.")

for protocol in active_protocols:
    st.markdown(f"---\n### 📄 {protocol}")

    try:
        df = xl.parse(protocol)
    except Exception as e:
        st.warning(f"Could not read '{protocol}': {e}")
        continue

    if df.empty:
        st.info("This sheet is empty.")
        continue

    existing = existing_df[existing_df["protocol"] == protocol]

    default_rename = int(existing["rename_row"].iloc[0]) if not existing.empty and "rename_row" in existing else 0
    rename_row = st.number_input(
        f"Row to rename columns (0-indexed):", min_value=0, max_value=len(df)-1,
        value=default_rename, key=f"rename_{protocol}"
    )

    # Attempt to use the selected rename_row as headers
    raw_headers = df.iloc[rename_row].astype(str).fillna("").tolist()

    # Warn if most headers are empty
    non_empty_headers = [h for h in raw_headers if h.strip() != ""]
    if len(non_empty_headers) < len(raw_headers) * 0.5:
        st.warning(f"⚠️ Selected rename row ({rename_row}) for {protocol} appears mostly empty. You may need to pick a different row.")

    # Deduplicate column names
    from collections import Counter
    counts = Counter(raw_headers)
    seen = {}

    def make_unique(col):
        if col.strip() == "":
            col = "unnamed"
        if counts[col] > 1:
            count = seen.get(col, 0) + 1
            seen[col] = count
            return f"{col}_{count}"
        return col

    df.columns = [make_unique(c) for c in raw_headers]
    df = df.iloc[rename_row + 1:].reset_index(drop=True)

    default_cols = existing["original_column"].unique().tolist() if not existing.empty else list(df.columns[:3])
    selected_cols = st.multiselect(
        f"Select columns to keep:", options=list(df.columns), default=default_cols, key=f"cols_{protocol}"
    )

    default_rows = existing["row_index"].unique().tolist() if not existing.empty else list(df.index[:3])
    selected_rows = st.multiselect(
        f"Select rows to keep (by index):", options=list(df.index[:20]), default=default_rows, key=f"rows_{protocol}"
    )

    existing_desc = existing["description"].dropna().iloc[0] if "description" in existing.columns and not existing.empty else ""
    description = st.text_area("Optional notes:", value=existing_desc, key=f"desc_{protocol}")

    if selected_cols and selected_rows:
        try:
            df_preview = df.loc[selected_rows, selected_cols]
            st.dataframe(df_preview, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not display preview table: {e}")

        for row in selected_rows:
            for col in selected_cols:
                rowcol_data.append({
                    "protocol": protocol,
                    "row_index": row,
                    "original_column": col,
                    "rename_row": rename_row,
                    "description": description
                })
    else:
        st.info("⚠️ No rows or columns selected for this protocol. Nothing will be saved.")

# Save all collected selections
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
        st.warning("Nothing was selected to save. Please review your protocols.")
