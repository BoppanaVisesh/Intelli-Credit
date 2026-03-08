"""
Create Sample Test Files for Manual Upload
==========================================

This script creates realistic GST and Bank Statement files
that you can upload through the frontend UI.
"""

import pandas as pd
import os
from datetime import datetime

# Create test data directory
os.makedirs("./test_data", exist_ok=True)

print("\n" + "="*80)
print("📁 CREATING SAMPLE TEST FILES")
print("="*80)

# ============================================================================
# SCENARIO 1: EXCELLENT COMPANY
# ============================================================================
print("\n1️⃣  Creating files for EXCELLENT COMPANY (Expected Score: 85-95)")
print("-" * 80)

# GST Returns - Excellent
gst_excellent = {
    'Month': ['Apr-2025', 'May-2025', 'Jun-2025', 'Jul-2025', 'Aug-2025', 'Sep-2025',
              'Oct-2025', 'Nov-2025', 'Dec-2025', 'Jan-2026', 'Feb-2026', 'Mar-2026'],
    'GSTR-1 Sales (₹ Cr)': [4.2, 4.5, 4.8, 5.1, 5.3, 5.5, 5.8, 6.0, 6.2, 6.5, 6.8, 7.0],
    'GSTR-3B Sales (₹ Cr)': [4.1, 4.4, 4.7, 5.0, 5.2, 5.4, 5.7, 5.9, 6.1, 6.4, 6.7, 6.9],
    'GSTR-2A Purchases (₹ Cr)': [2.5, 2.7, 2.9, 3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.9, 4.0, 4.2],
    'Input Tax Credit (₹ Lakhs)': [45, 48, 52, 56, 58, 60, 63, 65, 67, 70, 72, 75],
    'GST Paid (₹ Lakhs)': [30, 32, 34, 36, 38, 39, 41, 42, 44, 46, 48, 49]
}
df_gst_ex = pd.DataFrame(gst_excellent)
totals = {
    'Month': 'TOTAL',
    'GSTR-1 Sales (₹ Cr)': df_gst_ex['GSTR-1 Sales (₹ Cr)'].sum(),
    'GSTR-3B Sales (₹ Cr)': df_gst_ex['GSTR-3B Sales (₹ Cr)'].sum(),
    'GSTR-2A Purchases (₹ Cr)': df_gst_ex['GSTR-2A Purchases (₹ Cr)'].sum(),
    'Input Tax Credit (₹ Lakhs)': df_gst_ex['Input Tax Credit (₹ Lakhs)'].sum(),
    'GST Paid (₹ Lakhs)': df_gst_ex['GST Paid (₹ Lakhs)'].sum()
}
df_gst_ex = pd.concat([df_gst_ex, pd.DataFrame([totals])], ignore_index=True)
filename1 = "./test_data/GST_Returns_TechCorp_Excellent.xlsx"
df_gst_ex.to_excel(filename1, index=False, sheet_name='GST Returns')
print(f"✅ {filename1}")
print(f"   Annual Sales: ₹{totals['GSTR-1 Sales (₹ Cr)']:.2f} Cr (Growing trend)")
print(f"   Variance: {abs(totals['GSTR-1 Sales (₹ Cr)'] - totals['GSTR-3B Sales (₹ Cr)']) / totals['GSTR-1 Sales (₹ Cr)'] * 100:.1f}% (Very low)")

# Bank Statement - Excellent
bank_excellent = {
    'Date': ['01-Apr-2025', '01-May-2025', '01-Jun-2025', '01-Jul-2025', '01-Aug-2025', 
             '01-Sep-2025', '01-Oct-2025', '01-Nov-2025', '01-Dec-2025', '01-Jan-2026',
             '01-Feb-2026', '01-Mar-2026'],
    'Description': ['Sales Receipts'] * 12,
    'Credit (₹ Cr)': [4.0, 4.3, 4.6, 4.9, 5.1, 5.3, 5.6, 5.8, 6.0, 6.3, 6.6, 6.8],
    'Debit (₹ Cr)': [2.4, 2.6, 2.8, 3.0, 3.1, 3.2, 3.4, 3.5, 3.6, 3.8, 3.9, 4.1],
    'Balance (₹ Cr)': [1.6, 3.3, 5.1, 7.0, 9.0, 11.1, 13.3, 15.6, 18.0, 20.5, 23.2, 25.9]
}
df_bank_ex = pd.DataFrame(bank_excellent)
filename2 = "./test_data/Bank_Statement_TechCorp_Excellent.xlsx"
df_bank_ex.to_excel(filename2, index=False, sheet_name='Bank Statement')
print(f"✅ {filename2}")
print(f"   Annual Inflows: ₹{sum(bank_excellent['Credit (₹ Cr)']):.2f} Cr")
print(f"   Closing Balance: ₹{bank_excellent['Balance (₹ Cr)'][-1]:.2f} Cr (Strong)")

# ============================================================================
# SCENARIO 2: AVERAGE COMPANY
# ============================================================================
print("\n2️⃣  Creating files for AVERAGE COMPANY (Expected Score: 60-75)")
print("-" * 80)

# GST Returns - Average
gst_average = {
    'Month': ['Apr-2025', 'May-2025', 'Jun-2025', 'Jul-2025', 'Aug-2025', 'Sep-2025',
              'Oct-2025', 'Nov-2025', 'Dec-2025', 'Jan-2026', 'Feb-2026', 'Mar-2026'],
    'GSTR-1 Sales (₹ Cr)': [3.2, 2.8, 3.5, 3.0, 3.3, 2.9, 3.4, 3.1, 3.6, 3.2, 3.5, 3.3],
    'GSTR-3B Sales (₹ Cr)': [3.0, 2.7, 3.3, 2.9, 3.1, 2.8, 3.2, 3.0, 3.4, 3.1, 3.3, 3.2],
    'GSTR-2A Purchases (₹ Cr)': [2.0, 1.8, 2.2, 1.9, 2.1, 1.9, 2.2, 2.0, 2.3, 2.1, 2.3, 2.2],
    'Input Tax Credit (₹ Lakhs)': [36, 32, 40, 34, 38, 34, 40, 36, 41, 38, 41, 40],
    'GST Paid (₹ Lakhs)': [18, 16, 20, 17, 19, 17, 19, 18, 20, 19, 20, 19]
}
df_gst_avg = pd.DataFrame(gst_average)
totals = {
    'Month': 'TOTAL',
    'GSTR-1 Sales (₹ Cr)': df_gst_avg['GSTR-1 Sales (₹ Cr)'].sum(),
    'GSTR-3B Sales (₹ Cr)': df_gst_avg['GSTR-3B Sales (₹ Cr)'].sum(),
    'GSTR-2A Purchases (₹ Cr)': df_gst_avg['GSTR-2A Purchases (₹ Cr)'].sum(),
    'Input Tax Credit (₹ Lakhs)': df_gst_avg['Input Tax Credit (₹ Lakhs)'].sum(),
    'GST Paid (₹ Lakhs)': df_gst_avg['GST Paid (₹ Lakhs)'].sum()
}
df_gst_avg = pd.concat([df_gst_avg, pd.DataFrame([totals])], ignore_index=True)
filename3 = "./test_data/GST_Returns_MidTier_Average.xlsx"
df_gst_avg.to_excel(filename3, index=False, sheet_name='GST Returns')
print(f"✅ {filename3}")
print(f"   Annual Sales: ₹{totals['GSTR-1 Sales (₹ Cr)']:.2f} Cr (Stable/volatile)")
print(f"   Variance: {abs(totals['GSTR-1 Sales (₹ Cr)'] - totals['GSTR-3B Sales (₹ Cr)']) / totals['GSTR-1 Sales (₹ Cr)'] * 100:.1f}% (Moderate)")

# Bank Statement - Average
bank_average = {
    'Date': ['01-Apr-2025', '01-May-2025', '01-Jun-2025', '01-Jul-2025', '01-Aug-2025',
             '01-Sep-2025', '01-Oct-2025', '01-Nov-2025', '01-Dec-2025', '01-Jan-2026',
             '01-Feb-2026', '01-Mar-2026'],
    'Description': ['Sales Receipts'] * 12,
    'Credit (₹ Cr)': [2.9, 2.6, 3.2, 2.8, 3.0, 2.7, 3.1, 2.9, 3.3, 3.0, 3.2, 3.1],
    'Debit (₹ Cr)': [1.9, 1.7, 2.1, 1.8, 2.0, 1.8, 2.1, 1.9, 2.2, 2.0, 2.2, 2.1],
    'Balance (₹ Cr)': [1.0, 1.9, 3.0, 4.0, 5.0, 5.9, 6.9, 7.9, 9.0, 10.0, 11.0, 12.0]
}
df_bank_avg = pd.DataFrame(bank_average)
filename4 = "./test_data/Bank_Statement_MidTier_Average.xlsx"
df_bank_avg.to_excel(filename4, index=False, sheet_name='Bank Statement')
print(f"✅ {filename4}")
print(f"   Annual Inflows: ₹{sum(bank_average['Credit (₹ Cr)']):.2f} Cr")
print(f"   Closing Balance: ₹{bank_average['Balance (₹ Cr)'][-1]:.2f} Cr (Moderate)")

# ============================================================================
# SCENARIO 3: POOR/RISKY COMPANY
# ============================================================================
print("\n3️⃣  Creating files for RISKY COMPANY (Expected Score: 10-40)")
print("-" * 80)

# GST Returns - Poor
gst_poor = {
    'Month': ['Apr-2025', 'May-2025', 'Jun-2025', 'Jul-2025', 'Aug-2025', 'Sep-2025',
              'Oct-2025', 'Nov-2025', 'Dec-2025', 'Jan-2026', 'Feb-2026', 'Mar-2026'],
    'GSTR-1 Sales (₹ Cr)': [2.5, 1.8, 3.2, 1.5, 2.8, 1.9, 2.6, 1.7, 3.0, 1.6, 2.7, 2.0],
    'GSTR-3B Sales (₹ Cr)': [2.0, 1.5, 2.8, 1.2, 2.4, 1.6, 2.2, 1.4, 2.6, 1.3, 2.3, 1.7],
    'GSTR-2A Purchases (₹ Cr)': [2.8, 2.2, 3.5, 2.0, 3.0, 2.3, 2.9, 2.1, 3.2, 2.0, 3.0, 2.5],
    'Input Tax Credit (₹ Lakhs)': [50, 40, 63, 36, 54, 41, 52, 38, 58, 36, 54, 45],
    'GST Paid (₹ Lakhs)': [12, 9, 17, 7, 14, 10, 13, 8, 16, 8, 14, 10]
}
df_gst_poor = pd.DataFrame(gst_poor)
totals = {
    'Month': 'TOTAL',
    'GSTR-1 Sales (₹ Cr)': df_gst_poor['GSTR-1 Sales (₹ Cr)'].sum(),
    'GSTR-3B Sales (₹ Cr)': df_gst_poor['GSTR-3B Sales (₹ Cr)'].sum(),
    'GSTR-2A Purchases (₹ Cr)': df_gst_poor['GSTR-2A Purchases (₹ Cr)'].sum(),
    'Input Tax Credit (₹ Lakhs)': df_gst_poor['Input Tax Credit (₹ Lakhs)'].sum(),
    'GST Paid (₹ Lakhs)': df_gst_poor['GST Paid (₹ Lakhs)'].sum()
}
df_gst_poor = pd.concat([df_gst_poor, pd.DataFrame([totals])], ignore_index=True)
filename5 = "./test_data/GST_Returns_Struggling_Risky.xlsx"
df_gst_poor.to_excel(filename5, index=False, sheet_name='GST Returns')
print(f"✅ {filename5}")
print(f"   Annual Sales: ₹{totals['GSTR-1 Sales (₹ Cr)']:.2f} Cr (Highly volatile)")
print(f"   Variance: {abs(totals['GSTR-1 Sales (₹ Cr)'] - totals['GSTR-3B Sales (₹ Cr)']) / totals['GSTR-1 Sales (₹ Cr)'] * 100:.1f}% (HIGH - Red flag!)")

# Bank Statement - Poor (MISALIGNED with GST!)
bank_poor = {
    'Date': ['01-Apr-2025', '01-May-2025', '01-Jun-2025', '01-Jul-2025', '01-Aug-2025',
             '01-Sep-2025', '01-Oct-2025', '01-Nov-2025', '01-Dec-2025', '01-Jan-2026',
             '01-Feb-2026', '01-Mar-2026'],
    'Description': ['Sales Receipts'] * 12,
    'Credit (₹ Cr)': [1.8, 1.3, 2.4, 1.1, 2.0, 1.4, 1.9, 1.2, 2.3, 1.2, 2.0, 1.5],  # Much lower than GST!
    'Debit (₹ Cr)': [2.7, 2.1, 3.4, 1.9, 2.9, 2.2, 2.8, 2.0, 3.1, 1.9, 2.9, 2.4],  # Higher than credit!
    'Balance (₹ Cr)': [-0.9, -1.7, -2.7, -3.5, -4.4, -5.2, -6.1, -6.9, -7.7, -8.4, -9.3, -10.2]  # Negative!
}
df_bank_poor = pd.DataFrame(bank_poor)
filename6 = "./test_data/Bank_Statement_Struggling_Risky.xlsx"
df_bank_poor.to_excel(filename6, index=False, sheet_name='Bank Statement')
print(f"✅ {filename6}")
print(f"   Annual Inflows: ₹{sum(bank_poor['Credit (₹ Cr)']):.2f} Cr")
print(f"   Closing Balance: ₹{bank_poor['Balance (₹ Cr)'][-1]:.2f} Cr (NEGATIVE! 🚨)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("✅ ALL TEST FILES CREATED SUCCESSFULLY!")
print("="*80)
print("\n📂 Files location: backend/test_data/")
print("\n📋 How to use these files:")
print("\n  OPTION 1: Upload via UI")
print("  -------------------------")
print("  1. Open http://localhost:3000")
print("  2. Click 'New Application'")
print("  3. Upload ONE GST file + ONE Bank file")
print("  4. Fill company details:")
print("     - For Excellent: Name='TechCorp Industries', Sector='Technology'")
print("     - For Average: Name='MidTier Manufacturing', Sector='Manufacturing'")
print("     - For Risky: Name='Struggling Enterprises', Sector='Steel Trading'")
print("  5. Click Submit and see the results!")
print("\n  OPTION 2: Test via API (Python)")
print("  ---------------------------------")
print("  Use the script: test_real_file_uploads.py")
print("  (But backend must be running)")
print("\n📊 Expected Results:")
print("  ✅ Excellent Company → Score: 85-95, Decision: APPROVE")
print("  ⚠️  Average Company  → Score: 60-75, Decision: APPROVE with conditions")
print("  ❌ Risky Company    → Score: 10-40, Decision: REJECT")
print("\n🔍 Verification:")
print("  - Different companies should get DIFFERENT scores")
print("  - System should detect GST-Bank variance (high for risky company)")
print("  - Web research should find REAL articles about the company/sector")
print("  - Credit Officer notes should affect the score")
print("\n🎯 Ready to test! Use these REAL files to verify the system works correctly.")
print("="*80 + "\n")
