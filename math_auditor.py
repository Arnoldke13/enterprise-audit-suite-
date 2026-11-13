def audit_invoice(vendor, tax_pin, sub_total, tax_amount, claimed_total, min_pin_length=11):
    expected_total = round(sub_total + tax_amount, 2)
    difference = round(claimed_total - expected_total, 2)
    flags = []

    if min_pin_length > 0 and (not tax_pin or len(str(tax_pin).strip()) < min_pin_length):
        flags.append(f"Invalid Tax PIN (Needs {min_pin_length}+ chars)")
    if difference != 0:
        flags.append(f"Math Off by {difference}")

    status = "PASSED" if not flags else "FLAGGED"
    return {
        "Vendor": vendor,
        "Expected": expected_total,
        "Claimed": claimed_total,
        "Status": status,
        "Flags": ", ".join(flags) if flags else "None"
    }
