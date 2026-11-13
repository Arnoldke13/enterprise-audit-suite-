def check_duplicates(invoice_list):
    seen = set()
    for inv in invoice_list:
        vendor_name = inv.get("Vendor") or inv.get("vendor", "")
        claimed_amt = inv.get("Claimed") or inv.get("claimed_total", 0)
        key = (str(vendor_name).strip().lower(), claimed_amt)
        if key in seen:
            inv["Duplicate"] = "FLAGGED: Duplicate"
        else:
            seen.add(key)
            inv["Duplicate"] = "PASSED"
    return invoice_list
