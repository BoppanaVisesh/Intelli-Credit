"""
Seed the database with 3 demo applications so teammates get pre-loaded data.
Called automatically on server startup if the DB is empty.
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
]


def seed_demo_applications():
    """Insert demo applications if the DB is empty."""
    db = SessionLocal()
    try:
        count = db.query(Application).count()
        if count > 0:
            print(f"   Database already has {count} application(s) — skipping seed")
            return

        for app_data in DEMO_APPS:
            app = Application(**app_data)
            db.add(app)

        db.commit()
        print(f"   ✅ Seeded {len(DEMO_APPS)} demo applications")
    except Exception as e:
        db.rollback()
        print(f"   ⚠️ Seed failed: {e}")
    finally:
        db.close()
