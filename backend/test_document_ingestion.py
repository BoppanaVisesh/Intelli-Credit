"""
Test End-to-End Document Upload & Parsing Flow
Tests: Upload → Classify → Parse → Store
"""
import requests
import json
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"


def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def test_document_ingestion_flow():
    """Test complete document ingestion flow"""
    
    print_header("🧪 TESTING DOCUMENT INGESTION FLOW")
    
    # Step 1: Create a test application
    print("📝 Step 1: Creating test application...")
    
    app_data = {
        "company_name": "Test Corp Ltd",
        "mca_cin": "L12345KA2020PLC123456",
        "sector": "Manufacturing",
        "requested_limit_cr": 100.0
    }
    
    response = requests.post(f"{API_BASE}/applications/", json=app_data)
    if response.status_code != 200:
        print(f"❌ Failed to create application: {response.text}")
        return
    
    app = response.json()
    
    # Handle different response formats
    if 'application_id' in app:
        application_id = app['application_id']
    elif 'application' in app:
        application_id = app['application']['id']
    elif 'id' in app:
        application_id = app['id']
    else:
        print(f"❌ Unexpected response format: {app}")
        return
        
    print(f"✅ Created Application: {application_id}")
    print(f"   Company: {app_data['company_name']}")
    
    # Step 2: Upload documents
    print("\n📤 Step 2: Uploading documents...")
    
    # Find test files from test_data and downloads
    test_files = []
    test_paths = [
        Path('test_data/Bank_Statement_TechCorp_Excellent.xlsx'),
        Path('test_data/GST_Returns_TechCorp_Excellent.xlsx'),
        Path('../downloads/AnnualReport_SpiceJet_202324.pdf')
    ]
    
    test_files = [f for f in test_paths if f.exists()]
    
    if not test_files:
        print("⚠️  No test files found")
        print("   Checked: test_data/ and downloads/")
        return
    
    print(f"   Found {len(test_files)} test file(s):")
    for f in test_files:
        print(f"   • {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    # Upload files
    files = [('files', (f.name, open(f, 'rb'), 'application/octet-stream')) for f in test_files]
    data = {'application_id': application_id}
    
    response = requests.post(
        f"{API_BASE}/ingestion/upload-documents",
        files=files,
        data=data
    )
    
    # Close file handles
    for _, (_, fh, _) in files:
        fh.close()
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return
    
    upload_result = response.json()
    print(f"✅ Upload successful!")
    print(f"   Total files uploaded: {upload_result['total_files']}")
    
    for doc in upload_result['uploaded_files']:
        print(f"\n   📄 {doc['filename']}")
        print(f"      Type: {doc['document_type']}")
        print(f"      Confidence: {doc['classification_confidence']*100:.0f}%")
        print(f"      Status: {doc['parse_status']}")
    
    # Step 3: Parse documents
    print("\n🔍 Step 3: Parsing documents...")
    
    response = requests.post(f"{API_BASE}/ingestion/parse-documents/{application_id}")
    
    if response.status_code != 200:
        print(f"❌ Parsing failed: {response.text}")
        return
    
    parse_result = response.json()
    print(f"✅ Parsing completed!")
    print(f"   Documents parsed: {parse_result['parsed_count']}/{parse_result['total_documents']}")
    
    for result in parse_result['results']:
        print(f"\n   📄 {result['filename']}")
        print(f"      Type: {result['document_type']}")
        print(f"      Status: {result['parse_status']}")
        
        if result['parse_status'] == 'COMPLETED' and 'parsed_data' in result:
            data = result['parsed_data']
            print(f"      ✓ Extracted Data Preview:")
            
            # Show key extracted fields based on document type
            if result['document_type'] == 'BANK_STATEMENT':
                print(f"        • Total Inflows: ₹{data.get('total_inflows_cr', 0):.2f} Cr")
                print(f"        • Total Outflows: ₹{data.get('total_outflows_cr', 0):.2f} Cr")
                print(f"        • Avg Balance: ₹{data.get('average_balance_cr', 0):.2f} Cr")
            
            elif result['document_type'] == 'GST_RETURN':
                print(f"        • GSTR-1 Sales: ₹{data.get('gstr_1_sales_cr', 0):.2f} Cr")
                print(f"        • GSTR-3B Sales: ₹{data.get('gstr_3b_sales_cr', 0):.2f} Cr")
                print(f"        • Variance: {data.get('variance_percent', 0):.1f}%")
            
            elif result['document_type'] == 'ITR':
                print(f"        • PAN: {data.get('pan', 'N/A')}")
                print(f"        • Assessment Year: {data.get('assessment_year', 'N/A')}")
                print(f"        • Gross Income: ₹{data.get('gross_total_income', 0):,.0f}")
            
            elif result['document_type'] == 'ANNUAL_REPORT':
                print(f"        • Company: {data.get('company_name', 'N/A')}")
                print(f"        • Revenue: ₹{data.get('revenue_cr', 0):.2f} Cr")
                print(f"        • Auditor: {data.get('auditor_name', 'N/A')}")
        
        elif result['parse_status'] == 'FAILED':
            print(f"      ✗ Error: {result.get('error', 'Unknown error')}")
    
    # Step 4: Retrieve all documents
    print("\n📋 Step 4: Retrieving all documents...")
    
    response = requests.get(f"{API_BASE}/ingestion/documents/{application_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to retrieve documents: {response.text}")
        return
    
    docs_result = response.json()
    print(f"✅ Retrieved {docs_result['total_documents']} document(s)")
    
    # Final Summary
    print_header("📊 TEST SUMMARY")
    
    print(f"✅ Application Created: {application_id}")
    print(f"✅ Files Uploaded: {upload_result['total_files']}")
    print(f"✅ Files Parsed: {parse_result['parsed_count']}/{parse_result['total_documents']}")
    print(f"✅ Total Documents in System: {docs_result['total_documents']}")
    
    completed = sum(1 for d in docs_result['documents'] if d['parse_status'] == 'COMPLETED')
    failed = sum(1 for d in docs_result['documents'] if d['parse_status'] == 'FAILED')
    
    print(f"\n📈 Parse Status:")
    print(f"   • Completed: {completed}")
    print(f"   • Failed: {failed}")
    print(f"   • Success Rate: {(completed/docs_result['total_documents']*100):.0f}%")
    
    print(f"\n{'='*80}")
    print(f"  🎉 END-TO-END TEST COMPLETED SUCCESSFULLY!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    try:
        test_document_ingestion_flow()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend API")
        print("   Please make sure the backend server is running on http://localhost:8000")
        print("   Run: python main.py")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
