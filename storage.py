# storage.py — Supabase-backed data handling for Streamlit app

from supabase import create_client, Client
import pandas as pd
import os

# Connect to Supabase
SUPABASE_URL = "https://dgqwazdsxqesiethlvuo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRncXdhemRzeHFlc2lldGhsdnVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxNDgxNDMsImV4cCI6MjA2NDcyNDE0M30.wG6x2AdL_Wlv_cgPU8n6aJOS38l6GZdi09W0acFNoi4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

### --- ACTIVE PROTOCOLS ---
def get_active_protocols():
    res = supabase.table("active_protocols").select("protocol").execute()
    return pd.DataFrame(res.data)

def set_active_protocols(protocol_list):
    # Clear then insert
    supabase.table("active_protocols").delete().neq("protocol", "").execute()
    insert_data = [{"protocol": p} for p in protocol_list]
    supabase.table("active_protocols").insert(insert_data).execute()


### --- ROW/COL MAP ---
def get_row_col_map():
    res = supabase.table("row_col_map").select("*").execute()
    return pd.DataFrame(res.data)

def set_row_col_map(df: pd.DataFrame):
    """Replace mappings for each protocol independently to avoid overwriting others."""
    for proto in df["protocol"].unique():
        subset = df[df["protocol"] == proto]
        supabase.table("row_col_map").delete().eq("protocol", proto).execute()
        if not subset.empty:
            supabase.table("row_col_map").insert(subset.to_dict(orient="records")).execute()


### --- ATTESTATION LOG ---
def append_attestation_log(entry: dict):
    supabase.table("attestation_log").insert(entry).execute()

def get_attestation_log():
    res = supabase.table("attestation_log").select("*").order("timestamp", desc=True).execute()
    return pd.DataFrame(res.data)

def delete_attestation_rows(ids: list):
    for i in ids:
        supabase.table("attestation_log").delete().eq("id", i).execute()


### --- SITE LIST ---
def get_site_list():
    res = supabase.table("site_list").select("site").execute()
    return [r["site"] for r in res.data]

def set_site_list(sites: list):
    supabase.table("site_list").delete().neq("site", "").execute()
    data = [{"site": s} for s in sites]
    supabase.table("site_list").insert(data).execute()

def clear_row_col_map_for(protocols):
    for p in protocols:
        supabase.table("row_col_map").delete().eq("protocol", p).execute()
