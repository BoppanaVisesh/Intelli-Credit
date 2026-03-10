"""
Generate synthetic test data for 3 companies to test the full Intelli-Credit pipeline.

Company 1: Apex Manufacturing Pvt Ltd    → Healthy, should APPROVE
Company 2: GreenField Logistics Ltd      → GST fraud/mismatch, should REJECT
Company 3: Orion Retail Pvt Ltd          → Circular trading, should REJECT
"""
import os
import json
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent / "test_data"

# ─────────────────────────────────────────────────────────────────────
# Company 1 — Apex Manufacturing Pvt Ltd (HEALTHY)
# Revenue ~45 Cr, low debt, clean records → expect APPROVE
# ─────────────────────────────────────────────────────────────────────
APEX_DIR = BASE / "company1_apex_manufacturing"

APEX_ANNUAL_REPORT = {
    "company_name": "Apex Manufacturing Pvt Ltd",
    "financial_year": "2025-26",
    "revenue_cr": 45.0,
    "net_profit_cr": 5.2,
    "ebitda_cr": 8.5,
    "total_debt_cr": 10.0,
    "total_equity_cr": 25.0,
    "total_assets_cr": 55.0,
    "current_assets_cr": 22.0,
    "current_liabilities_cr": 12.0,
    "fixed_assets_cr": 33.0,
    "contingent_liabilities_cr": 0.5,
    "related_party_transactions_cr": 1.2,
    "auditor_name": "Deloitte Haskins & Sells LLP",
    "auditor_opinion": "Unqualified",
    "pending_litigations": [
        {"description": "Supplier payment dispute", "amount_cr": 0.5, "status": "pending"}
    ],
    "management_commentary": "Strong operational performance with 12% revenue growth YoY. Capacity utilization at 78%. Planning expansion into electric vehicle components.",
    "key_risks": ["Raw material price volatility", "Dependence on auto sector"],
    "expansion_plans": "New manufacturing facility in Pune, capex of 8 Cr planned for FY27"
}

# Monthly bank transactions — healthy, consistent cash flow
# Values in full rupees (parser divides by 1e7 to get Crores)
APEX_BANK_DATA = []
months = ["Jan-25","Feb-25","Mar-25","Apr-25","May-25","Jun-25",
          "Jul-25","Aug-25","Sep-25","Oct-25","Nov-25","Dec-25"]
# ~45 Cr annual inflow → ~3.75 Cr/month → 3,75,00,000 per month
credit_amounts = [38000000, 36500000, 40000000, 37500000, 35000000, 39000000,
                  41000000, 37000000, 38500000, 36000000, 42000000, 39500000]
debit_amounts  = [32000000, 30500000, 33000000, 31000000, 29000000, 33500000,
                  34000000, 31500000, 32000000, 30000000, 35000000, 33000000]

# Diverse customer base (healthy pattern — NOT concentrated on cycle partners)
apex_customers = [
    "Metro Auto Parts Ltd", "Reliable Traders Pvt Ltd", "Orion Retail Pvt Ltd",
    "Supreme Components Ltd", "National Motors Pvt Ltd", "Metro Auto Parts Ltd",
    "Quality Engineers India", "Orion Retail Pvt Ltd", "Premier Auto Spares",
    "Supreme Components Ltd", "National Motors Pvt Ltd", "Reliable Traders Pvt Ltd",
]
apex_vendors = [
    "Steel Corp India Pvt Ltd", "GreenField Logistics Ltd", "Supreme Raw Materials",
    "Power Grid Utilities", "Steel Corp India Pvt Ltd", "National Packaging Ltd",
    "GreenField Logistics Ltd", "Industrial Chemicals Co", "Steel Corp India Pvt Ltd",
    "Supreme Raw Materials", "Power Grid Utilities", "National Packaging Ltd",
]

balance = 5000000
for i, month in enumerate(months):
    # Sales credit — from named customers
    balance += credit_amounts[i]
    APEX_BANK_DATA.append({
        "Date": f"15-{month.split('-')[0].lower()}-2025",
        "Description": f"NEFT from {apex_customers[i]} {month}",
        "Debit": 0,
        "Credit": credit_amounts[i],
        "Balance": balance
    })
    # Vendor payment — to named vendors
    balance -= debit_amounts[i]
    APEX_BANK_DATA.append({
        "Date": f"25-{month.split('-')[0].lower()}-2025",
        "Description": f"RTGS to {apex_vendors[i]} {month}",
        "Debit": debit_amounts[i],
        "Credit": 0,
        "Balance": balance
    })
    # Salary payment
    salary = 3000000
    balance -= salary
    APEX_BANK_DATA.append({
        "Date": f"28-{month.split('-')[0].lower()}-2025",
        "Description": f"Salary payment {month}",
        "Debit": salary,
        "Credit": 0,
        "Balance": balance
    })

# GST Returns — consistent, small variance (healthy)
# ~45 Cr annual sales → ~3.75 Cr/month → 37500000
APEX_GST_DATA = []
gstr1_sales = [38000000, 36500000, 40000000, 37500000, 35000000, 39000000,
               41000000, 37000000, 38500000, 36000000, 42000000, 39500000]
for i, month in enumerate(months):
    APEX_GST_DATA.append({
        "Month": month,
        "GSTR-1 Sales": gstr1_sales[i],
        "GSTR-3B Sales": int(gstr1_sales[i] * 0.98),  # Tiny 2% variance — normal
        "Purchases": int(gstr1_sales[i] * 0.65),
    })

# Apex GST invoice-level data — diverse customer/supplier base (healthy)
APEX_GSTR1_INVOICES = []  # Outward supplies (sales)
apex_gst_buyers = [
    ("Metro Auto Parts Ltd", "27AABCM1234A1ZC"),
    ("Reliable Traders Pvt Ltd", "29AADCR5678B1ZB"),
    ("Orion Retail Pvt Ltd", "07AAACO4567D1ZE"),
    ("Supreme Components Ltd", "33AABCS9012E1ZA"),
    ("National Motors Pvt Ltd", "09AABCN3456F1ZD"),
]
for i, month in enumerate(months):
    buyer = apex_gst_buyers[i % len(apex_gst_buyers)]
    taxable = gstr1_sales[i]
    APEX_GSTR1_INVOICES.append({
        "Invoice_No": f"AP/INV/{i+1:03d}/2025",
        "Invoice_Date": f"15-{month.split('-')[0]}-2025",
        "Buyer_Name": buyer[0],
        "Buyer_GSTIN": buyer[1],
        "Taxable_Value": taxable,
        "Tax_Amount": int(taxable * 0.18),
        "Invoice_Value": int(taxable * 1.18),
    })

APEX_GSTR2A_INVOICES = []  # Inward supplies (purchases)
apex_gst_suppliers = [
    ("Steel Corp India Pvt Ltd", "27AABCS7890G1ZF"),
    ("GreenField Logistics Ltd", "06AADCG2345H1ZG"),
    ("Supreme Raw Materials", "33AABCS4567J1ZH"),
    ("Industrial Chemicals Co", "29AAICI1234K1ZI"),
    ("Power Grid Utilities", "09AABCP6789L1ZJ"),
]
for i, month in enumerate(months):
    supplier = apex_gst_suppliers[i % len(apex_gst_suppliers)]
    taxable = int(gstr1_sales[i] * 0.65)
    APEX_GSTR2A_INVOICES.append({
        "Invoice_No": f"SUP/{i+1:03d}/2025",
        "Invoice_Date": f"10-{month.split('-')[0]}-2025",
        "Supplier_Name": supplier[0],
        "Supplier_GSTIN": supplier[1],
        "Taxable_Value": taxable,
        "Tax_Amount": int(taxable * 0.18),
        "Invoice_Value": int(taxable * 1.18),
    })


# ─────────────────────────────────────────────────────────────────────
# Company 2 — GreenField Logistics Ltd (GST FRAUD)
# GST shows 60 Cr sales but bank only shows 20 Cr inflows
# Massive mismatch → expect REJECT
# ─────────────────────────────────────────────────────────────────────
GREENFIELD_DIR = BASE / "company2_greenfield_logistics"

GREENFIELD_ANNUAL_REPORT = {
    "company_name": "GreenField Logistics Ltd",
    "financial_year": "2025-26",
    "revenue_cr": 60.0,
    "net_profit_cr": 2.0,
    "ebitda_cr": 4.0,
    "total_debt_cr": 35.0,
    "total_equity_cr": 8.0,
    "total_assets_cr": 50.0,
    "current_assets_cr": 18.0,
    "current_liabilities_cr": 22.0,
    "fixed_assets_cr": 32.0,
    "contingent_liabilities_cr": 5.0,
    "related_party_transactions_cr": 12.0,
    "auditor_name": "Sharp & Associates",
    "auditor_opinion": "Qualified",
    "pending_litigations": [
        {"description": "GST evasion notice from DGGI", "amount_cr": 3.5, "status": "pending"},
        {"description": "Customer breach of contract", "amount_cr": 2.0, "status": "pending"},
        {"description": "Labour court case", "amount_cr": 0.8, "status": "pending"}
    ],
    "management_commentary": "Revenue grew 40% driven by new route expansions. Focus on fleet modernization.",
    "key_risks": ["High fuel costs", "Driver attrition", "Regulatory changes in transport sector"],
    "expansion_plans": "Expanding to 5 new cities in FY27"
}

# Bank statement — only 20 Cr actual inflows (vs 60 Cr GST sales!)
GREENFIELD_BANK_DATA = []
balance = 2000000
gf_credit = [17000000, 16000000, 18000000, 15000000, 16500000, 17500000,
             18500000, 16000000, 17000000, 15500000, 19000000, 17000000]
gf_debit  = [15000000, 14500000, 16000000, 13500000, 14800000, 16000000,
             17000000, 14500000, 15500000, 14000000, 17500000, 15500000]

# GreenField receives from Apex (for logistics services) and pays Orion
gf_customers = [
    "Apex Manufacturing Pvt Ltd", "Quick Transport Corp", "Apex Manufacturing Pvt Ltd",
    "Highway Movers India", "Quick Transport Corp", "Apex Manufacturing Pvt Ltd",
    "National Freight Carriers", "Highway Movers India", "Apex Manufacturing Pvt Ltd",
    "Quick Transport Corp", "National Freight Carriers", "Apex Manufacturing Pvt Ltd",
]
gf_vendors = [
    "Orion Retail Pvt Ltd", "Diesel Suppliers India", "Fleet Maintenance Corp",
    "Orion Retail Pvt Ltd", "Diesel Suppliers India", "Orion Retail Pvt Ltd",
    "Fleet Maintenance Corp", "Diesel Suppliers India", "Orion Retail Pvt Ltd",
    "Fleet Maintenance Corp", "Diesel Suppliers India", "Orion Retail Pvt Ltd",
]

for i, month in enumerate(months):
    balance += gf_credit[i]
    GREENFIELD_BANK_DATA.append({
        "Date": f"10-{month.split('-')[0].lower()}-2025",
        "Description": f"NEFT from {gf_customers[i]} {month}",
        "Debit": 0,
        "Credit": gf_credit[i],
        "Balance": balance
    })
    balance -= gf_debit[i]
    GREENFIELD_BANK_DATA.append({
        "Date": f"20-{month.split('-')[0].lower()}-2025",
        "Description": f"RTGS to {gf_vendors[i]} {month}",
        "Debit": gf_debit[i],
        "Credit": 0,
        "Balance": balance
    })
    # Bounced cheque every other month — red flag
    if i % 2 == 0:
        GREENFIELD_BANK_DATA.append({
            "Date": f"22-{month.split('-')[0].lower()}-2025",
            "Description": f"CHEQUE RETURN - insufficient funds {month}",
            "Debit": 0,
            "Credit": 0,
            "Balance": balance
        })

# GST Returns — inflated! 60 Cr claimed (5 Cr/month) but bank shows only 20 Cr
GREENFIELD_GST_DATA = []
gf_gstr1 = [50000000, 48000000, 52000000, 49000000, 51000000, 53000000,
            55000000, 50000000, 52000000, 48000000, 54000000, 51000000]
for i, month in enumerate(months):
    GREENFIELD_GST_DATA.append({
        "Month": month,
        "GSTR-1 Sales": gf_gstr1[i],
        "GSTR-3B Sales": int(gf_gstr1[i] * 0.85),  # 15% internal mismatch too
        "Purchases": int(gf_gstr1[i] * 0.90),  # Suspiciously high purchase ratio
    })

# GreenField GST invoice-level data — shows cycle participants
GREENFIELD_GSTR1_INVOICES = []
gf_gst_buyers = [
    ("Orion Retail Pvt Ltd", "07AAACO4567D1ZE"),
    ("Quick Transport Corp", "33AABCQ7890M1ZK"),
    ("Orion Retail Pvt Ltd", "07AAACO4567D1ZE"),
    ("Highway Movers India", "27AABCH3456N1ZL"),
    ("Orion Retail Pvt Ltd", "07AAACO4567D1ZE"),
]
for i, month in enumerate(months):
    buyer = gf_gst_buyers[i % len(gf_gst_buyers)]
    taxable = gf_gstr1[i]
    GREENFIELD_GSTR1_INVOICES.append({
        "Invoice_No": f"GF/INV/{i+1:03d}/2025",
        "Invoice_Date": f"12-{month.split('-')[0]}-2025",
        "Buyer_Name": buyer[0],
        "Buyer_GSTIN": buyer[1],
        "Taxable_Value": taxable,
        "Tax_Amount": int(taxable * 0.18),
        "Invoice_Value": int(taxable * 1.18),
    })

GREENFIELD_GSTR2A_INVOICES = []
gf_gst_suppliers = [
    ("Apex Manufacturing Pvt Ltd", "27AABCA1234Z1ZA"),
    ("Diesel Suppliers India", "09AABCD5678P1ZM"),
    ("Apex Manufacturing Pvt Ltd", "27AABCA1234Z1ZA"),
    ("Fleet Maintenance Corp", "33AABCF9012Q1ZN"),
    ("Apex Manufacturing Pvt Ltd", "27AABCA1234Z1ZA"),
]
for i, month in enumerate(months):
    supplier = gf_gst_suppliers[i % len(gf_gst_suppliers)]
    taxable = int(gf_gstr1[i] * 0.90)
    GREENFIELD_GSTR2A_INVOICES.append({
        "Invoice_No": f"SUP/{i+1:03d}/2025",
        "Invoice_Date": f"08-{month.split('-')[0]}-2025",
        "Supplier_Name": supplier[0],
        "Supplier_GSTIN": supplier[1],
        "Taxable_Value": taxable,
        "Tax_Amount": int(taxable * 0.18),
        "Invoice_Value": int(taxable * 1.18),
    })


# ─────────────────────────────────────────────────────────────────────
# Company 3 — Orion Retail Pvt Ltd (CIRCULAR TRADING)
# Transactions form a cycle: Apex → Orion → GreenField → Apex
# Purchases ≈ Sales (round-tripping), minimal cash retention
# ─────────────────────────────────────────────────────────────────────
ORION_DIR = BASE / "company3_orion_retail"

ORION_ANNUAL_REPORT = {
    "company_name": "Orion Retail Pvt Ltd",
    "financial_year": "2025-26",
    "revenue_cr": 30.0,
    "net_profit_cr": 0.5,
    "ebitda_cr": 1.5,
    "total_debt_cr": 20.0,
    "total_equity_cr": 10.0,
    "total_assets_cr": 35.0,
    "current_assets_cr": 15.0,
    "current_liabilities_cr": 14.0,
    "fixed_assets_cr": 20.0,
    "contingent_liabilities_cr": 3.0,
    "related_party_transactions_cr": 18.0,  # Huge related party — red flag
    "auditor_name": "M/s Dubious & Co",
    "auditor_opinion": "Qualified",
    "pending_litigations": [
        {"description": "NCLT case - oppression and mismanagement", "amount_cr": 5.0, "status": "pending"},
        {"description": "Tax dispute with IT department", "amount_cr": 2.5, "status": "pending"}
    ],
    "management_commentary": "Expanding retail operations. Strong supplier network.",
    "key_risks": ["Thin margins", "High working capital requirement", "Concentrated customer base"],
    "expansion_plans": "Opening 10 new stores in FY27"
}

# Bank statement — inflows ≈ outflows (minimal retention, round-tripping signal)
ORION_BANK_DATA = []
balance = 1000000
# ~30 Cr inflows, ~29 Cr outflows — nearly zero retention
or_credit = [25000000, 24000000, 26000000, 25500000, 24500000, 26500000,
             25000000, 24000000, 25500000, 24500000, 27000000, 25000000]
or_debit  = [24500000, 23500000, 25500000, 25000000, 24000000, 26000000,
             24500000, 23500000, 25000000, 24000000, 26500000, 24500000]

for i, month in enumerate(months):
    # Inflows from "GreenField Logistics" — circular
    balance += or_credit[i]
    ORION_BANK_DATA.append({
        "Date": f"05-{month.split('-')[0].lower()}-2025",
        "Description": f"NEFT from GreenField Logistics Ltd {month}",
        "Debit": 0,
        "Credit": or_credit[i],
        "Balance": balance
    })
    # Outflows to "Apex Manufacturing" — circular
    balance -= or_debit[i]
    ORION_BANK_DATA.append({
        "Date": f"10-{month.split('-')[0].lower()}-2025",
        "Description": f"NEFT to Apex Manufacturing Pvt Ltd {month}",
        "Debit": or_debit[i],
        "Credit": 0,
        "Balance": balance
    })

# GST — purchases ≈ sales (round-tripping indicator)
ORION_GST_DATA = []
or_gstr1 = [25000000, 24000000, 26000000, 25500000, 24500000, 26500000,
            25000000, 24000000, 25500000, 24500000, 27000000, 25000000]
for i, month in enumerate(months):
    ORION_GST_DATA.append({
        "Month": month,
        "GSTR-1 Sales": or_gstr1[i],
        "GSTR-3B Sales": or_gstr1[i],    # Exactly matching — unusual
        "Purchases": int(or_gstr1[i] * 0.97),  # 97% purchase-to-sales ratio — round-tripping
    })

# Orion GST invoice-level data — concentrated on cycle participants (red flag!)
# Orion sells to GreenField, buys from Apex → circular: Apex → Orion → GreenField → Apex
ORION_GSTR1_INVOICES = []
orion_gst_buyers = [
    ("GreenField Logistics Ltd", "06AADCG2345H1ZG"),  # Primary buyer in the cycle
    ("GreenField Logistics Ltd", "06AADCG2345H1ZG"),
    ("Small Retail Shop", "07AAACS1234R1ZO"),          # Token legitimate buyer
    ("GreenField Logistics Ltd", "06AADCG2345H1ZG"),
    ("GreenField Logistics Ltd", "06AADCG2345H1ZG"),
]
for i, month in enumerate(months):
    buyer = orion_gst_buyers[i % len(orion_gst_buyers)]
    taxable = or_gstr1[i]
    ORION_GSTR1_INVOICES.append({
        "Invoice_No": f"OR/INV/{i+1:03d}/2025",
        "Invoice_Date": f"05-{month.split('-')[0]}-2025",
        "Buyer_Name": buyer[0],
        "Buyer_GSTIN": buyer[1],
        "Taxable_Value": taxable,
        "Tax_Amount": int(taxable * 0.18),
        "Invoice_Value": int(taxable * 1.18),
    })

ORION_GSTR2A_INVOICES = []
orion_gst_suppliers = [
    ("Apex Manufacturing Pvt Ltd", "27AABCA1234Z1ZA"),  # Primary supplier in the cycle
    ("Apex Manufacturing Pvt Ltd", "27AABCA1234Z1ZA"),
    ("Local Packaging Mart", "07AAACL5678S1ZP"),        # Token legitimate supplier
    ("Apex Manufacturing Pvt Ltd", "27AABCA1234Z1ZA"),
    ("Apex Manufacturing Pvt Ltd", "27AABCA1234Z1ZA"),
]
for i, month in enumerate(months):
    supplier = orion_gst_suppliers[i % len(orion_gst_suppliers)]
    taxable = int(or_gstr1[i] * 0.97)
    ORION_GSTR2A_INVOICES.append({
        "Invoice_No": f"SUP/{i+1:03d}/2025",
        "Invoice_Date": f"03-{month.split('-')[0]}-2025",
        "Supplier_Name": supplier[0],
        "Supplier_GSTIN": supplier[1],
        "Taxable_Value": taxable,
        "Tax_Amount": int(taxable * 0.18),
        "Invoice_Value": int(taxable * 1.18),
    })


def generate_all():
    """Generate all test data files."""
    for company_dir, annual_report, bank_data, gst_data, gstr1_inv, gstr2a_inv, label in [
        (APEX_DIR, APEX_ANNUAL_REPORT, APEX_BANK_DATA, APEX_GST_DATA,
         APEX_GSTR1_INVOICES, APEX_GSTR2A_INVOICES, "Apex (Healthy)"),
        (GREENFIELD_DIR, GREENFIELD_ANNUAL_REPORT, GREENFIELD_BANK_DATA, GREENFIELD_GST_DATA,
         GREENFIELD_GSTR1_INVOICES, GREENFIELD_GSTR2A_INVOICES, "GreenField (GST Fraud)"),
        (ORION_DIR, ORION_ANNUAL_REPORT, ORION_BANK_DATA, ORION_GST_DATA,
         ORION_GSTR1_INVOICES, ORION_GSTR2A_INVOICES, "Orion (Circular Trading)"),
    ]:
        print(f"\n{'='*60}")
        print(f"  Generating test data: {label}")
        print(f"{'='*60}")

        os.makedirs(company_dir, exist_ok=True)

        # Annual Report (JSON)
        ar_path = company_dir / "annual_report.json"
        with open(ar_path, "w", encoding="utf-8") as f:
            json.dump(annual_report, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {ar_path.name}")

        # Bank Statement (XLSX)
        bank_path = company_dir / "bank_statement.xlsx"
        df_bank = pd.DataFrame(bank_data)
        df_bank.to_excel(bank_path, index=False, sheet_name="Transactions")
        print(f"  ✓ {bank_path.name}  ({len(bank_data)} rows)")

        # GST Returns (XLSX) — multi-sheet with invoice-level counterparty data
        gst_path = company_dir / "gst_returns.xlsx"
        with pd.ExcelWriter(gst_path, engine="openpyxl") as writer:
            pd.DataFrame(gst_data).to_excel(writer, index=False, sheet_name="GST_Summary")
            pd.DataFrame(gstr1_inv).to_excel(writer, index=False, sheet_name="GSTR1_Outward")
            pd.DataFrame(gstr2a_inv).to_excel(writer, index=False, sheet_name="GSTR2A_Inward")
        print(f"  ✓ {gst_path.name}  ({len(gst_data)} summary + {len(gstr1_inv)} outward + {len(gstr2a_inv)} inward rows)")

    print(f"\n{'='*60}")
    print("  All test data generated successfully!")
    print(f"{'='*60}")


if __name__ == "__main__":
    generate_all()
