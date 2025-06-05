# Shared path config
import os
BASE_DIR = "data"
os.makedirs(BASE_DIR, exist_ok=True)  # Ensure directory exists

ACTIVE_PROTOCOLS_FILE = os.path.join(BASE_DIR, "active_protocols.csv")
ROWCOL_SELECTION_FILE = os.path.join(BASE_DIR, "protocol_row_col_map.csv")
ATTEST_LOG = os.path.join(BASE_DIR, "attestation_log.csv")
LOCK_FILE = os.path.join(BASE_DIR, "locked.flag")
SITE_LIST_FILE = os.path.join(BASE_DIR, "site_list.csv")
SHEET_IMAGES_DIR = "sheet_images"  # Assuming images are static and committed
EXCEL_FILE = "protocol_sections.xlsx"  # Also assumed committed
