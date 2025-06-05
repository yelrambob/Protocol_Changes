import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Protocol Change History")

LOG_FILE = "change_log.csv"

if not os.path.exists(LOG_FILE):
    st.info("No history recorded yet.")
    st.stop()

df_log = pd.read_csv(LOG_FILE)

if df_log.empty:
    st.info("No history recorded yet.")
    st.stop()

# --- Search Filter ---
search_query = st.text_input("🔍 Search protocol name (partial matches allowed):").strip().lower()

# --- Timestamp Selector ---
timestamps = df_log["Timestamp"].dropna().unique()
selected_ts = st.selectbox("🕒 View changes from timestamp:", options=sorted(timestamps, reverse=True))

# --- Filtered View ---
df_filtered = df_log[df_log["Timestamp"] == selected_ts]

if search_query:
    df_filtered = df_filtered[df_filtered["Protocol"].str.lower().str.contains(search_query)]

if df_filtered.empty:
    st.warning("No matching protocols found for this timestamp.")
else:
    st.markdown(f"### Showing {len(df_filtered)} change(s) from `{selected_ts}`")
    st.dataframe(df_filtered, use_container_width=True)

    # --- Export ---
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download This Entry to CSV", csv, f"protocol_changes_{selected_ts}.csv", "text/csv")

# --- Delete ---
if st.button("🗑️ Delete All Changes from This Timestamp"):
    df_log = df_log[df_log["Timestamp"] != selected_ts]
    df_log.to_csv(LOG_FILE, index=False)
    st.success("Deleted entry successfully. Refresh the page to update view.")
