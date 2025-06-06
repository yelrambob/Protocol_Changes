from supabase import create_client, Client
import pandas as pd

# 🔑 Supabase credentials
SUPABASE_URL = "https://dgqwazdsxqesiethlvuo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRncXdhemRzeHFlc2lldGhsdnVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxNDgxNDMsImV4cCI6MjA2NDcyNDE0M30.wG6x2AdL_Wlv_cgPU8n6aJOS38l6GZdi09W0acFNoi4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 📥 Get current active protocols
def get_active_protocols():
    res = supabase.table("active_protocols").select("*").execute()
    df = pd.DataFrame(res.data)
    return df if not df.empty else pd.DataFrame(columns=["protocol"])

# 📤 Set active protocols (replaces all entries)
def set_active_protocols(df):
    supabase.table("active_protocols").delete().neq("protocol", "").execute()
    if not df.empty:
        supabase.table("active_protocols").insert(df.to_dict(orient="records")).execute()

# 📥 Get saved row/column selections
def get_row_col_map():
    res = supabase.table("row_col_map").select("*").execute()
    df = pd.DataFrame(res.data)
    return df if not df.empty else pd.DataFrame(columns=["protocol", "row_index", "original_column", "rename_row", "description"])

# ✅ Save only one protocol's mapping at a time (preserve others)
def replace_protocol_mapping(protocol, df_subset):
    supabase.table("row_col_map").delete().eq("protocol", protocol).execute()
    if not df_subset.empty:
        supabase.table("row_col_map").insert(df_subset.to_dict(orient="records")).execute()

# 🗑 Clear all saved row/col mappings (if ever needed)
def clear_all_row_col_map():
    supabase.table("row_col_map").delete().neq("protocol", "").execute()

# 🧪 Optional: Debug helper to list protocols with saved mappings
def get_saved_protocols():
    df = get_row_col_map()
    return df["protocol"].unique().tolist() if not df.empty else []
