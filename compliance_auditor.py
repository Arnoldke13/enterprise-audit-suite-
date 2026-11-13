def audit_compliance(sub_total, tax_amount, approval_code="", vat_rate=0.16, approval_limit=50000):
    flags = []
    expected_tax = round(sub_total * vat_rate, 2)

    if round(tax_amount, 2) != expected_tax:
        flags.append(f"Tax Mismatch (Expected {expected_tax})")
    if sub_total > approval_limit and not str(approval_code).strip():
        flags.append(f"Over {approval_limit:,.0f}: Missing Approval Code")

    return "PASSED" if not flags else ", ".join(flags)
