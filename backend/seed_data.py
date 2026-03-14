"""
Seed the database with demo applications so teammates get pre-loaded data.
Called automatically on server startup.
"""
from core.database import SessionLocal
from models.application import Application, ApplicationStatus
from datetime import datetime

DEMO_APPS = [
    {
        "id": "DEMO-APEX-001",
        "company_name": "Apex Manufacturing Pvt Ltd",
        "mca_cin": "U28110MH2015PTC265432",
        "pan": "AABCA1234Z",
        "sector": "Manufacturing",
        "incorporation_date": "2015-06-12",
        "registered_address": "Plot 42, MIDC Industrial Area, Pune, Maharashtra 411019",
        "annual_turnover_cr": 45.0,
        "employee_count": 320,
        "promoter_names": "Rajesh Mehta, Sunita Mehta",
        "requested_limit_cr": 10.0,
        "loan_type": "Working Capital",
        "loan_tenure_months": 12,
        "interest_type": "Floating",
        "collateral_offered": "Factory land and machinery valued at 18 Cr",
        "purpose_of_loan": "Working capital for expansion into EV components manufacturing",
        "existing_banking": "State Bank of India — CC limit 5 Cr (since 2018)",
        "status": ApplicationStatus.PENDING,
    },
    {
        "id": "DEMO-GREENFIELD-002",
        "company_name": "GreenField Logistics Ltd",
        "mca_cin": "U60100DL2018PLC328745",
        "pan": "AADCG2345H",
        "sector": "Logistics",
        "incorporation_date": "2018-03-22",
        "registered_address": "B-14, Transport Nagar, Dwarka, New Delhi 110075",
        "annual_turnover_cr": 60.0,
        "employee_count": 180,
        "promoter_names": "Vikram Singh Chauhan",
        "requested_limit_cr": 15.0,
        "loan_type": "Term Loan",
        "loan_tenure_months": 60,
        "interest_type": "Fixed",
        "collateral_offered": "Fleet of 50 commercial vehicles",
        "purpose_of_loan": "Fleet expansion and route modernisation",
        "existing_banking": "ICICI Bank — CC limit 8 Cr (since 2020)",
        "status": ApplicationStatus.PENDING,
    },
    {
        "id": "DEMO-ORION-003",
        "company_name": "Orion Retail Pvt Ltd",
        "mca_cin": "U52100KA2019PTC354321",
        "pan": "AAACO4567D",
        "sector": "Retail",
        "incorporation_date": "2019-08-10",
        "registered_address": "No. 7, Commercial Street, Bangalore, Karnataka 560001",
        "annual_turnover_cr": 30.0,
        "employee_count": 95,
        "promoter_names": "Anand Rao, Priya Rao",
        "requested_limit_cr": 8.0,
        "loan_type": "CC/OD",
        "loan_tenure_months": 12,
        "interest_type": "Floating",
        "collateral_offered": "Commercial property valued at 12 Cr",
        "purpose_of_loan": "Inventory financing and store expansion",
        "existing_banking": "HDFC Bank — OD limit 3 Cr (since 2021)",
        "status": ApplicationStatus.PENDING,
    },
    {
        "id": "DEMO-KINARA-004",
        "company_name": "Kinara Capital Private Limited",
        "mca_cin": "U65923KA1996PTC020518",
        "pan": "AABCK1234K",
        "sector": "NBFC",
        "incorporation_date": "1996-05-14",
        "registered_address": "No. 50, 100 Feet Road, HAL II Stage, Indiranagar, Bengaluru 560038",
        "annual_turnover_cr": 723.0,
        "employee_count": 2000,
        "promoter_names": "Hardika Shah, Kalpana Sankar",
        "requested_limit_cr": 12.0,
        "loan_type": "Term Loan",
        "loan_tenure_months": 36,
        "interest_type": "Floating",
        "collateral_offered": "Receivables and pooled MSME portfolio",
        "purpose_of_loan": "Growth capital for MSME portfolio expansion",
        "existing_banking": "Multiple institutional lenders",
        "status": ApplicationStatus.PENDING,
    },
    {
        "id": "DEMO-TATA-005",
        "company_name": "Tata Capital Limited",
        "mca_cin": "U65990MH1991PLC060670",
        "pan": "AAACT1234T",
        "sector": "NBFC",
        "incorporation_date": "1991-03-10",
        "registered_address": "Tower A, Peninsula Business Park, Lower Parel, Mumbai 400013",
        "annual_turnover_cr": 28369.0,
        "employee_count": 10000,
        "promoter_names": "Tata Sons Private Limited",
        "requested_limit_cr": 20.0,
        "loan_type": "Working Capital",
        "loan_tenure_months": 24,
        "interest_type": "Floating",
        "collateral_offered": "Corporate guarantees and diversified book",
        "purpose_of_loan": "On-lending and business growth",
        "existing_banking": "Large consortium borrowing profile",
        "status": ApplicationStatus.PENDING,
    },
    {
        "id": "DEMO-MONEYBOXX-006",
        "company_name": "Moneyboxx Finance Limited",
        "mca_cin": "L65999DL1994PLC061485",
        "pan": "AABCM1234M",
        "sector": "NBFC",
        "incorporation_date": "1994-02-18",
        "registered_address": "New Delhi, India",
        "annual_turnover_cr": 721.0,
        "employee_count": 1000,
        "promoter_names": "Dilip Singh, Deepak Aggarwal",
        "requested_limit_cr": 25.0,
        "loan_type": "Working Capital",
        "loan_tenure_months": 24,
        "interest_type": "Floating",
        "collateral_offered": "Receivables and lending book assets",
        "purpose_of_loan": "On-lending and portfolio growth",
        "existing_banking": "Institutional debt lines and diversified borrowing",
        "status": ApplicationStatus.PENDING,
    },
    {
        "id": "DEMO-VIVRITI-007",
        "company_name": "Vivriti Capital Limited",
        "mca_cin": "U67190TN2007PLC065149",
        "pan": "AABCV1234V",
        "sector": "NBFC",
        "incorporation_date": "2007-11-20",
        "registered_address": "Chennai, Tamil Nadu, India",
        "annual_turnover_cr": 1200.0,
        "employee_count": 500,
        "promoter_names": "Gaurav Kumar, R Sridhar",
        "requested_limit_cr": 8.0,
        "loan_type": "Term Loan",
        "loan_tenure_months": 24,
        "interest_type": "Floating",
        "collateral_offered": "Corporate assets and receivables",
        "purpose_of_loan": "Balance sheet growth and lending operations",
        "existing_banking": "Multiple lender relationships and debt market access",
        "status": ApplicationStatus.PENDING,
    },
]


def seed_demo_applications():
    """Insert missing demo applications. Safe to run repeatedly."""
    db = SessionLocal()
    try:
        inserted = 0
        for app_data in DEMO_APPS:
            existing = db.query(Application).filter(Application.id == app_data["id"]).first()
            if existing:
                continue
            app = Application(**app_data)
            db.add(app)
            inserted += 1

        db.commit()
        if inserted:
            print(f"   ✅ Seeded {inserted} demo application(s)")
        else:
            print("   Database already contains all demo applications — skipping seed")
    except Exception as e:
        db.rollback()
        print(f"   ⚠️ Seed failed: {e}")
    finally:
        db.close()
