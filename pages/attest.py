import streamlit as st
import pandas as pd
from datetime import datetime
import json

# --- Constants ---
CHANGE_LOG = "protocol_change_log.csv"
ATTEST_LOG = "attestations.csv"

# --- Query ---
query_params = st.experimental_get_query_params()
protocol_raw = query_params.get("protocol", [""])[0]
protocol = protocol_raw.replace("_", " ")

st.title("✅ Protocol Change Attestation")

if not protocol:
    st.warning("No protocol specified in the URL. Use /attest?protocol=Your_Protocol_Name")
    st.stop()

st.header(f"Review Changes for: {protocol}")

# --- Load Data ---
if not pd.read_csv(CHANGE_LOG).empty:
    df = pd.read_csv(CHANGE_LOG)
    match = df[df["Protocol"] == protocol]

    if match.empty:
        st.error(f"No change record found for protocol: {protocol}")
        st.stop()
    else:
        row = match.iloc[-1]  # Use latest change if duplicates

        # Display change info
        st.subheader("📋 Parameters Updated")
        param_cols = [
            "Body Part", "Phase", "Plane", "Angle", "Algorithm",
            "Thickness/Interval", "Archive Destinations",
            "Body Part per Phase"
        ]
        for col in param_cols:
            st.markdown(f"**{col}**: {row[col]}")

        # Show required series
        st.subheader("📑 Required Series Table")
        try:
            series_df = pd.read_json(row["Required Series"])
            st.dataframe(series_df, use_container_width=True)
        except Exception:
            st.text("No valid series table found.")

        st.markdown("---")
        st.subheader("🖊 Attestation Form")
        name = st.text_input("Your Name")
        site = st.text_input("Your Site")
        confirm = st.checkbox("I attest that I have reviewed and will apply these changes.")

        if st.button("Submit Attestation"):
            if not name or not site or not confirm:
                st.warning("All fields and checkbox must be completed.")
            else:
                new_attest = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Protocol": protocol,
                    "Name": name,
                    "Site": site
                }

                if pd.read_csv(ATTEST_LOG).empty:
                    log_df = pd.DataFrame([new_attest])
                else:
                    log_df = pd.read_csv(ATTEST_LOG)
                    log_df = pd.concat([log_df, pd.DataFrame([new_attest])], ignore_index=True)

                log_df.to_csv(ATTEST_LOG, index=False)
                st.success("Your attestation has been recorded. Thank you.")
else:
    st.error("No protocol change data found. Please submit changes first.")
# Please submit changes first to generate the change log.
# If you need to submit changes, use the admin interface.   
