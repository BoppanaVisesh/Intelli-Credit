# 🎯 QUICK TEST GUIDE - USE THESE FILES NOW!

## 📍 Files Location
```
d:\my projects\inteli cred\Intelli-Credit\backend\test_data\
```

## ✅ Test Files Summary

### File 1: Excellent Company (Score: 85-95 expected)
- **GST:** `GST_Returns_TechCorp_Excellent.xlsx`
  - Sales: ₹4.2 Cr → ₹7.0 Cr (growing every month)
  - GSTR-1 vs GSTR-3B variance: ~1.5% (very low - good!)
  - Total annual: ₹65.5 Cr

- **Bank:** `Bank_Statement_TechCorp_Excellent.xlsx`
  - Inflows: ₹4.0 Cr → ₹6.8 Cr (aligned with GST)
  - Closing balance: ₹25.9 Cr (POSITIVE - excellent liquidity!)
  - Consistent cash surplus

### File 2: Average Company (Score: 60-75 expected)
- **GST:** `GST_Returns_MidTier_Average.xlsx`
  - Sales: ₹2.8 Cr - ₹3.6 Cr (volatile but manageable)
  - GSTR-1 vs GSTR-3B variance: ~5.2%
  - Total annual: ₹38.8 Cr

- **Bank:** `Bank_Statement_MidTier_Average.xlsx`
  - Inflows: ₹2.6 Cr - ₹3.3 Cr
  - Closing balance: ₹12.0 Cr (positive but moderate)
  - Some payment delays visible

### File 3: Risky Company (Score: 10-40 expected)
- **GST:** `GST_Returns_Struggling_Risky.xlsx`
  - Sales: ₹1.5 Cr - ₹3.2 Cr (HIGHLY VOLATILE 🚨)
  - GSTR-1 vs GSTR-3B variance: ~15.6% (RED FLAG!)
  - Total annual: ₹27.3 Cr

- **Bank:** `Bank_Statement_Struggling_Risky.xlsx`
  - Inflows: ₹1.1 Cr - ₹2.4 Cr (much LOWER than GST! 🚨)
  - Closing balance: **-₹10.2 Cr (NEGATIVE!)** ❌
  - Cash outflows > Inflows (burning cash!)

---

## 🧪 TEST NOW - Step by Step

### Step 1: Upload Excellent Company

1. **Go to:** http://localhost:3000
2. **Click:** "New Application" or "Data Ingestion"
3. **Upload Documents:**
   - GST Returns: Browse → `GST_Returns_TechCorp_Excellent.xlsx`
   - Bank Statement: Browse → `Bank_Statement_TechCorp_Excellent.xlsx`
4. **Fill Details:**
   ```
   Company Name: TechCorp Industries Ltd
   CIN: L72200KA2020PLC134567
   Sector: Technology
   Requested Limit: 15.0 (Cr)
   Credit Officer Notes: Strong revenue growth. Modern infrastructure observed during site visit.
   ```
5. **Click:** "Submit" or "Analyze"
6. **Wait:** 30-60 seconds (system is doing REAL web research!)
7. **Check Results:**
   - ✅ Score should be: **85-95/100**
   - ✅ Decision: **APPROVE**
   - ✅ Risk Grade: **A or B+**
   - ✅ Recommended Limit: **₹12-13 Cr** (80-85% of request)

### Step 2: Upload Risky Company (For Comparison)

1. **Create New Application**
2. **Upload Documents:**
   - GST: `GST_Returns_Struggling_Risky.xlsx`
   - Bank: `Bank_Statement_Struggling_Risky.xlsx`
3. **Fill Details:**
   ```
   Company Name: Struggling Enterprises Ltd
   CIN: L27106MP2018PLC045123
   Sector: Steel Trading
   Requested Limit: 20.0 (Cr)
   Credit Officer Notes: Factory operating at 40% capacity. Delayed payments to suppliers noted.
   ```
4. **Submit and Check:**
   - ✅ Score should be: **10-40/100** (much LOWER!)
   - ✅ Decision: **REJECT**
   - ✅ Risk Grade: **C or D**
   - ✅ Key Flags: Negative cash flow, GST-Bank mismatch, sector risk

---

## 🔍 What to Verify (Proves it's NOT dummy data)

### ✅ Data Extraction is REAL:
- [ ] System shows correct GST totals (₹65.5 Cr vs ₹27.3 Cr)
- [ ] System detects bank balance (₹25.9 Cr vs -₹10.2 Cr)
- [ ] System calculates variance correctly (1.5% vs 15.6%)

### ✅ Scores are DIFFERENT and LOGICAL:
- [ ] Excellent company gets HIGH score (85-95)
- [ ] Risky company gets LOW score (10-40)
- [ ] Scores are NOT the same (proves dynamic!)

### ✅ Web Research is REAL:
- [ ] System finds actual news articles (via Tavily API)
- [ ] Different companies get DIFFERENT articles
- [ ] Sentiment analysis varies based on news

### ✅ Credit Officer Notes AFFECT Score:
- [ ] Add positive note → Score increases
- [ ] Add negative note ("factory at 40%") → Score decreases by 10-20 points
- [ ] This proves PRIMARY INSIGHT INTEGRATION works!

### ✅ Decision Explanation is COMPLETE:
- [ ] CAM document mentions the Five Cs
- [ ] Shows specific financial ratios from uploaded files
- [ ] Explains WHY decision was made (not generic)

---

## 📊 Expected Results Summary

| Metric | Excellent | Average | Risky |
|--------|-----------|---------|-------|
| **Credit Score** | 85-95 | 60-75 | 10-40 |
| **Decision** | APPROVE | CONDITIONAL | REJECT |
| **Risk Grade** | A/B+ | B/C+ | C/D |
| **GST Variance** | 1.5% ✅ | 5.2% ⚠️ | 15.6% ❌ |
| **Bank Balance** | +₹25.9 Cr ✅ | +₹12 Cr ⚠️ | -₹10.2 Cr ❌ |
| **Cash Flow** | Positive ✅ | Stable ⚠️ | Negative ❌ |

---

## 💡 Pro Tips

1. **Test Credit Officer Notes:**
   - First upload: "Excellent infrastructure"
   - See score: (e.g., 88)
   - Second upload: "Factory at 40% capacity, supplier delays"
   - See score drop: (e.g., 68) ← THIS PROVES IT WORKS!

2. **Check CAM Document:**
   - Download the Word document
   - Verify it mentions YOUR specific numbers (not generic)
   - Look for actual GST totals in the memo

3. **Compare All 3:**
   - Upload all 3 scenarios
   - Verify scores: Excellent > Average > Risky
   - This PROVES system is not returning static scores!

---

## 🎉 SUCCESS CRITERIA

Your system is working with REAL data if:

✅ **Different files → Different scores** (not same score every time)
✅ **Good company scores HIGH** (85-95)
✅ **Bad company scores LOW** (10-40)
✅ **Negative bank balance** detected in risky company
✅ **GST-Bank variance** correctly calculated
✅ **Web search** returns actual article titles
✅ **Credit Officer notes** change the score (±10-20 points)
✅ **CAM document** includes YOUR specific numbers

---

## 🚀 START TESTING NOW!

**File Location:** 
```
d:\my projects\inteli cred\Intelli-Credit\backend\test_data\
```

**Frontend URL:**
```
http://localhost:3000
```

**Backend Status:**
```powershell
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**You now have REAL files with REAL data to prove your system works!** 🎯
