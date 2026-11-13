import os
import json
import streamlit as st
import pandas as pd
from math_auditor import audit_invoice
from compliance_auditor import audit_compliance
from duplicate_detector import check_duplicates
from organizer import save_report

st.set_page_config(page_title="Enterprise Audit Suite", layout="wide")

# ==========================================
# 1. PASSWORD SECURITY GATE
# ==========================================
# Add or remove client access codes here anytime
VALID_ACCESS_CODES = {
    "ADMIN2026": "Master Admin",
    "CLIENT-01": "Apex Supplies Ltd",
    "VIP-AUDIT": "Premium Client"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["client_label"] = ""

if not st.session_state["authenticated"]:
    st.title("Enterprise Audit & Compliance Suite")
    st.subheader("Authorized Client Access Only")
    st.write("Please enter your licensed access code to unlock the audit engine.")

    entered_code = st.text_input("Access Code", type="password")
    if st.button("Unlock System"):
        if entered_code.strip() in VALID_ACCESS_CODES:
            st.session_state["authenticated"] = True
            st.session_state["client_label"] = VALID_ACCESS_CODES[entered_code.strip()]
            st.rerun()
        else:
            st.error("Invalid Access Code. Contact the system administrator to purchase a license.")
    st.stop()  # Stops the rest of the app from loading until unlocked!

# ==========================================
# 2. DYNAMIC RULES ENGINE (UNLOCKED)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "rules_config.json")

DEFAULT_RULES = {
    "Standard Corporate (16% VAT)": {
        "vat_rate": 16.0,
        "approval_limit": 50000,
        "require_pin": True,
        "min_pin_length": 11,
        "check_duplicates": True
    },
    "Zero-Rated / NGO (0% VAT)": {
        "vat_rate": 0.0,
        "approval_limit": 100000,
        "require_pin": True,
        "min_pin_length": 11,
        "check_duplicates": True
    },
    "Petty Cash / Small Retail": {
        "vat_rate": 16.0,
        "approval_limit": 5000,
        "require_pin": False,
        "min_pin_length": 0,
        "check_duplicates": False
    }
}

def load_rules():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_RULES, f, indent=2)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_rules(rules_dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(rules_dict, f, indent=2)

def to_clean_float(val):
    if pd.isna(val):
        return 0.0
    cleaned = str(val).replace(",", "").replace("$", "").replace("Ksh", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

st.title("Dynamic Enterprise Audit & Compliance Suite")
st.caption(f"Licensed Session: {st.session_state['client_label']}")

# Logout button in sidebar
if st.sidebar.button("Lock / Log Out"):
    st.session_state["authenticated"] = False
    st.rerun()

rules = load_rules()

# 3. Sidebar: Client Branding & Dynamic Profiles
st.sidebar.header("1. Client Branding & Profile")
client_name = st.sidebar.text_input("Client Company Name", value="Acme Enterprises Ltd")
selected_preset = st.sidebar.selectbox("Select Company Profile", list(rules.keys()))
active = rules[selected_preset]

st.sidebar.header("2. Dynamic Audit Rules")
vat_rate = st.sidebar.number_input("VAT Rate (%)", value=float(active["vat_rate"]), step=1.0) / 100
approval_limit = st.sidebar.number_input("Manager Approval Limit", value=int(active["approval_limit"]), step=5000)
require_pin = st.sidebar.checkbox("Require Valid Tax PIN", value=bool(active["require_pin"]))
min_pin_len = st.sidebar.number_input("Minimum PIN Length", value=int(active["min_pin_length"]), step=1) if require_pin else 0
check_dups = st.sidebar.checkbox("Flag Duplicate Invoices", value=bool(active["check_duplicates"]))

with st.sidebar.expander("Save Upgrade as New Profile"):
    new_profile_name = st.text_input("New Profile Name (e.g., Construction 2027)")
    if st.button("Save Profile") and new_profile_name.strip():
        rules[new_profile_name.strip()] = {
            "vat_rate": vat_rate * 100,
            "approval_limit": approval_limit,
            "require_pin": require_pin,
            "min_pin_length": min_pin_len,
            "check_duplicates": check_dups
        }
        save_rules(rules)
        st.sidebar.success(f"Saved '{new_profile_name}'!")
        st.rerun()

# 4. Upload File & Case-Insensitive Column Auto-Detection
file = st.file_uploader("Upload Client Ledger (Excel or CSV)", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    cols = list(df.columns)
    lower_cols = [str(c).lower().strip().replace(" ", "_") for c in cols]

    def find_col(targets, offset=0):
        for t in targets:
            if t in lower_cols:
                return lower_cols.index(t) + offset
        return 0

    with st.expander("Match Client Columns (Auto-detected — click to adjust)", expanded=False):
        c1, c2, c3 = st.columns(3)
        col_vendor = c1.selectbox("Vendor Column", cols, index=find_col(["vendor", "supplier", "vendor_name", "supplier_name"]))
        col_pin = c2.selectbox("Tax PIN Column", ["None"] + cols, index=find_col(["tax_pin", "pin", "kra_pin", "vat_pin"], 1))
        col_sub = c3.selectbox("Sub-Total Column", cols, index=find_col(["sub_total", "subtotal", "net_amount", "amount"]))
        
        c4, c5, c6 = st.columns(3)
        col_tax = c4.selectbox("Tax Amount Column", cols, index=find_col(["tax_amount", "tax", "vat", "vat_amount"]))
        col_total = c5.selectbox("Claimed Total Column", cols, index=find_col(["claimed_total", "total", "gross_total", "grand_total"]))
        col_code = c6.selectbox("Approval Code Column", ["None"] + cols, index=find_col(["approval_code", "approval_id", "auth_code"], 1))

    if st.button("Run Full Audit"):
        results = []
        for _, r in df.iterrows():
            pin_val = "" if (col_pin == "None" or not require_pin or pd.isna(r[col_pin])) else str(r[col_pin]).strip()
            code_val = "" if (col_code == "None" or pd.isna(r[col_code])) else str(r[col_code]).strip()

            sub_val = to_clean_float(r[col_sub])
            tax_val = to_clean_float(r[col_tax])
            tot_val = to_clean_float(r[col_total])

            res = audit_invoice(
                str(r[col_vendor]),
                pin_val,
                sub_val,
                tax_val,
                tot_val,
                min_pin_length=min_pin_len
            )
            res["Compliance"] = audit_compliance(
                sub_val,
                tax_val,
                code_val,
                vat_rate=vat_rate,
                approval_limit=approval_limit
            )
            results.append(res)

        if check_dups:
            results = check_duplicates(results)
        else:
            for item in results:
                item["Duplicate"] = "SKIPPED"

        clean_filename = f"{client_name.strip().replace(' ', '_')}_Audit_Report.xlsx"
        clean, flagged, saved_money = save_report(results, client_name=client_name, output_file=clean_filename)

        st.subheader(f"Audit Summary: {client_name}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Clean Invoices", clean)
        col2.metric("Flagged Errors", flagged)
        col3.metric("Flagged Value At Risk", f"{saved_money:,.2f}")

        st.dataframe(pd.DataFrame(results), use_container_width=True)

        with open(clean_filename, "rb") as excel_file:
            st.download_button(
                label=f"Download {clean_filename}",
                data=excel_file,
                file_name=clean_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
