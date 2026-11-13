import pandas as pd
from datetime import datetime
from openpyxl.styles import Font

def save_report(records, client_name="Client Company", output_file="Audited_Report.xlsx"):
    df = pd.DataFrame(records)
    
    # Standardize column names to Title Case so 'status' or 'Status' both work
    df.columns = [str(c).strip().title() for c in df.columns]
    
    # Ensure required columns always exist
    for col in ["Status", "Compliance", "Duplicate"]:
        if col not in df.columns:
            df[col] = "PASSED"
    if "Claimed" not in df.columns:
        df["Claimed"] = 0.0

    is_clean = (
        (df["Status"] == "PASSED") & 
        (df["Compliance"] == "PASSED") & 
        (df["Duplicate"].isin(["PASSED", "SKIPPED"]))
    )
    
    clean_df = df[is_clean].copy()
    flagged_df = df[~is_clean].copy()
    flagged_amount = float(flagged_df["Claimed"].sum()) if not flagged_df.empty else 0.0
    audit_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        clean_df.to_excel(writer, sheet_name="Clean_Entries", index=False, startrow=4)
        flagged_df.to_excel(writer, sheet_name="Flagged_Items", index=False, startrow=4)

        for sheet_name in ["Clean_Entries", "Flagged_Items"]:
            ws = writer.sheets[sheet_name]
            ws["A1"] = f"OFFICIAL AUDIT REPORT: {client_name.upper()}"
            ws["A2"] = f"Audit Date: {audit_date} | Prepared by: Enterprise Audit Suite"
            ws["A3"] = f"Total Clean: {len(clean_df)} | Total Flagged: {len(flagged_df)} | Value At Risk: {flagged_amount:,.2f}"
            
            ws["A1"].font = Font(size=14, bold=True)
            ws["A2"].font = Font(size=10, italic=True)
            ws["A3"].font = Font(size=10, bold=True)

    return len(clean_df), len(flagged_df), round(flagged_amount, 2)
