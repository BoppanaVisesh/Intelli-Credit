# 🎯 REAL DATA TESTING GUIDE

## 📋 Quick Start: Test with Sample Files

### Option 1: Run the Automated Test Script (Recommended)

```powershell
# Navigate to backend
cd "d:\my projects\inteli cred\Intelli-Credit\backend"

# Install required packages (if not already installed)
pip install pandas openpyxl

# Run the comprehensive test
python test_real_file_uploads.py
```

**This will:**
✅ Create realistic GST returns (Excel files)
✅ Create realistic bank statements (Excel files)  
✅ Upload them through the API
✅ Show complete credit analysis results
✅ Save files in `./test_data/` folder for manual testing

---

## 📂 Option 2: Manual Testing with Created Files

After running the script above, you'll have **6 sample files** in `backend/test_data/`:

1. **GST Returns:**
   - `GST_Returns_TechCorp_Industries_Ltd_good.xlsx`
   - `GST_Returns_MidTier_Manufacturing_Pvt_Ltd_average.xlsx`
   - `GST_Returns_Struggling_Enterprises_Ltd_poor.xlsx`

2. **Bank Statements:**
   - `Bank_Statement_TechCorp_Industries_Ltd_good.xlsx`
   - `Bank_Statement_MidTier_Manufacturing_Pvt_Ltd_average.xlsx`
   - `Bank_Statement_Struggling_Enterprises_Ltd_poor.xlsx`

### Manual Upload Steps:

1. **Start Backend:**
   ```powershell
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Start Frontend:**
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Upload via UI:**
   - Go to http://localhost:3000
   - Click "New Application"
   - Upload GST + Bank Statement files
   - Enter company details
   - Click "Submit"

4. **View Results:**
   - See credit score calculated
   - Check web research results
   - View CAM document generated

---

## 🌐 Option 3: Test with REAL COMPANY DATA (Advanced)

### Where to Get Real Indian Company Documents:

#### 1. **GST Returns** (Sample Format)
**Create Your Own Test GST File:**

| Month | GSTR-1 Sales (₹) | GSTR-3B Sales (₹) | GSTR-2A Purchases (₹) | ITC (₹) | GST Paid (₹) |
|-------|------------------|-------------------|-----------------------|---------|--------------|
| Apr-25 | 4,20,00,000 | 4,10,00,000 | 2,50,00,000 | 45,00,000 | 30,00,000 |
| May-25 | 4,50,00,000 | 4,40,00,000 | 2,70,00,000 | 48,00,000 | 32,00,000 |
| ... | ... | ... | ... | ... | ... |

Save as Excel file with columns exactly as shown above.

#### 2. **Bank Statements** (Sample Format)

| Date | Description | Credit (₹) | Debit (₹) | Balance (₹) |
|------|-------------|-----------|----------|-------------|
| 01-04-2025 | Sales Receipt | 40,00,000 | | 40,00,000 |
| 05-04-2025 | Salary Payment | | 5,00,000 | 35,00,000 |
| ... | ... | ... | ... | ... |

Export from actual bank statement PDF (most banks allow Excel export).

#### 3. **Annual Reports** (Real Companies)

**Public Companies - Download from BSE/NSE:**

1. **Visit BSE Website:**
   - Go to: https://www.bseindia.com/
   - Search company name (e.g., "Reliance Industries")
   - Click "Corp Info" → "Annual Report"
   - Download latest PDF

2. **Visit NSE Website:**
   - Go to: https://www.nseindia.com/
   - Search company
   - Go to "Financial Results"
   - Download Annual Report

**Good Companies to Test:**
- **TCS** (Technology) - Strong financials
- **Infosys** (IT Services) - Excellent ratios
- **L&T** (Infrastructure) - Average complexity
- **Reliance Industries** (Conglomerate) - Large scale

#### 4. **MCA Documents** (Ministry of Corporate Affairs)

**Download Real Company Filings:**

1. Go to: http://www.mca.gov.in/mcafoportal/companyLLPMasterData.do
2. Enter CIN (e.g., L85110KA1992PLC013204 for Infosys)
3. Download:
   - Balance Sheet (Form AOC-4)
   - Director Details (Form DIR-12)
   - Charge Details

---

## 🔍 Test Scenarios

### Scenario 1: Excellent Company ⭐⭐⭐⭐⭐
```
Company: TechCorp Industries Ltd
Sector: Technology
GST Sales: Growing (₹4.2 Cr → ₹7.0 Cr)
Bank Alignment: <5% variance
Debt-to-Equity: 0.7
Expected Score: 85-95
Expected Decision: APPROVE
```

### Scenario 2: Average Company ⭐⭐⭐
```
Company: MidTier Manufacturing
Sector: Manufacturing
GST Sales: Stable (₹3.0 Cr - ₹3.5 Cr)
Bank Alignment: 8-12% variance
Debt-to-Equity: 1.75
Expected Score: 60-75
Expected Decision: APPROVE with conditions
```

### Scenario 3: High Risk Company ⚠️
```
Company: Struggling Enterprises
Sector: Steel Trading
GST Sales: Volatile (₹1.5 Cr - ₹3.2 Cr)
Bank Alignment: >20% variance
Debt-to-Equity: 14.0
Expected Score: 10-40
Expected Decision: REJECT
```

---

## 📊 What the System Actually Tests

### ✅ REAL Data Extraction

**1. GST Data Parsing:**
```python
# System extracts from Excel/PDF:
- Monthly sales (GSTR-1)
- Tax paid (GSTR-3B)
- Input tax credit (ITC)
- Purchase data (GSTR-2A)
- Calculates variance
```

**2. Circular Trading Detection:**
```python
# Analyzes transaction network:
- Repetitive transactions (A→B→C→A)
- Same amount patterns
- High frequency between parties
```

### ✅ REAL Web Research

**1. Promoter Background Check:**
```python
# Tavily API searches for:
- "Director Name + Litigation"
- "Director Name + Fraud"
- "Company + Scam"
# Returns REAL web articles
```

**2. Sector Risk Analysis:**
```python
# Searches for:
- "Sector + headwinds"
- "Sector + challenges 2026"
- "Industry outlook"
```

**3. Litigation Search:**
```python
# eCourts API checks:
- Civil cases
- Criminal cases
- NCLT proceedings
```

### ✅ REAL Sentiment Analysis

```python
# Gemini AI analyzes:
- News articles sentiment
- Director reputation
- Litigation severity
# NOT keyword matching - uses AI understanding
```

### ✅ REAL Credit Scoring

**Five Cs Framework:**
```
1. Character (30%)
   - Promoter sentiment: REAL web news
   - Litigation count: REAL court data
   
2. Capacity (25%)
   - DSCR: From ACTUAL bank statements
   - Cash flow: From REAL transactions
   
3. Capital (20%)
   - Debt-to-Equity: From ACTUAL balance sheet
   - Networth: From REAL annual report
   
4. Collateral (15%)
   - Asset coverage: From REAL financials
   
5. Conditions (10%)
   - Sector risk: From REAL web research
   - Economic factors: From REAL news
```

---

## 🎬 Expected Test Output

When you run `test_real_file_uploads.py`, you'll see:

```
================================================================================
🧪 TESTING WITH REAL FILES: TechCorp Industries Ltd (GOOD)
================================================================================

📄 Creating sample documents...
✅ Created GST file: ./test_data/GST_Returns_TechCorp_Industries_Ltd_good.xlsx
   Total Sales (GSTR-1): ₹65.50 Cr
   Variance: 1.89%

✅ Created Bank Statement: ./test_data/Bank_Statement_TechCorp_Industries_Ltd_good.xlsx
   Total Inflows: ₹62.30 Cr
   Total Outflows: ₹37.40 Cr

📤 Uploading documents to API...
   Company: TechCorp Industries Ltd
   Requested Limit: ₹15 Cr

================================================================================
📊 ANALYSIS RESULTS
================================================================================

🎯 CREDIT DECISION:
   Score: 88/100
   Decision: APPROVE
   Risk Grade: A
   Recommended Limit: ₹12.5 Cr
   Approval %: 83%

💼 FINANCIAL ANALYSIS:
   DSCR: 1.85
   Current Ratio: 2.0
   Debt-to-Equity: 0.70
   GST-Bank Variance: 4.89%
   Circular Trading Risk: 0

🌐 RESEARCH FINDINGS:
   Promoter Sentiment: POSITIVE
   Litigation Cases: 0
   Sector Risk: 25/100 (LOW)

📝 SUB-SCORES (5 Cs):
   Character    : 85/100 (weight: 30%)
   Capacity     : 90/100 (weight: 25%)
   Capital      : 88/100 (weight: 20%)
   Collateral   : 82/100 (weight: 15%)
   Conditions   : 75/100 (weight: 10%)

💡 KEY DECISION FACTORS:
   1. Strong cash flow with DSCR > 1.5
   2. Low debt-to-equity ratio indicates financial stability
   3. No adverse litigation found
   4. GST and bank records show consistency
   5. Sector outlook favorable

✅ TEST COMPLETED SUCCESSFULLY
   Files uploaded and processed
   Real data extracted from documents
   Web research conducted
   Credit score calculated dynamically
```

---

## 🔬 Verification Checklist

After testing, verify these aspects:

### ✅ Data Extraction
- [ ] GST totals match your input file
- [ ] Bank transactions summed correctly
- [ ] Financial ratios calculated from file data
- [ ] NOT using hardcoded values

### ✅ Web Research
- [ ] Search results show REAL article titles
- [ ] Different companies get DIFFERENT articles
- [ ] Sentiment reflects actual news content
- [ ] NOT returning dummy/static data

### ✅ Credit Scoring
- [ ] Scores change with different inputs
- [ ] Better company gets higher score
- [ ] Risky company gets lower score
- [ ] Sub-scores explain the final score

### ✅ Credit Officer Notes Impact
- [ ] Add note: "Factory at 40% capacity" → Score DECREASES
- [ ] Add note: "Expanding operations" → Score INCREASES
- [ ] Notes appear in CAM decision explanation

---

## 📞 Support

**If tests fail:**

1. **Check Backend Running:**
   ```powershell
   curl http://localhost:8000/health
   ```

2. **Check API Keys Set:**
   ```powershell
   # In backend/.env
   GEMINI_API_KEY=your_key_here
   TAVILY_API_KEY=your_key_here
   ```

3. **Check Logs:**
   ```powershell
   # Backend terminal will show errors
   ```

4. **Test Individual Components:**
   ```powershell
   python verify_complete_system.py
   ```

---

## 🎯 Success Criteria

**Your system is working correctly if:**

✅ **Different inputs produce different outputs**
✅ **Scores are logical** (Good > Average > Poor)
✅ **Web search returns real articles** (not dummy data)
✅ **Credit Officer notes affect the score** (Primary Insight Integration)
✅ **CAM document explains the decision** (Five Cs framework)
✅ **Files are actually parsed** (not ignored)

**Ready for hackathon demo when:**
✅ All tests pass with 85%+ pass rate
✅ UI shows complete credit analysis
✅ CAM downloads as professional Word document
✅ System responds to different company profiles correctly

---

## 🚀 Next Steps

1. **Run the test script** to create sample files
2. **Upload files via UI** to see visual output
3. **Try different scenarios** (good/average/poor companies)
4. **Test Credit Officer notes** to see score changes
5. **Download the CAM** to see professional output
6. **(Optional) Use real company data** from BSE/NSE for ultimate validation

**You now have REAL data to test with!** 🎉
