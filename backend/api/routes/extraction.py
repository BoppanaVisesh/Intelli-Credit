"""
Extraction & Schema Mapping Routes
- Review / approve / edit auto-classification
- CRUD for user-defined extraction schemas
- Run extraction against a schema
- Default schemas per document type
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid, json
from datetime import datetime

from api.dependencies import get_db
from core.config import get_settings
from models.uploaded_document import UploadedDocument, DocumentType, ParseStatus
from models.extraction_schema import ExtractionSchema

router = APIRouter()

# ───────────────────────── Default schemas per doc type ─────────────────────────

DEFAULT_SCHEMAS = {
    "ALM": {
        "name": "ALM — Asset-Liability Management",
        "fields": [
            {"key": "reporting_date", "label": "Reporting Date", "type": "date", "required": True},
            {"key": "total_assets", "label": "Total Assets (Cr)", "type": "number", "required": True},
            {"key": "total_liabilities", "label": "Total Liabilities (Cr)", "type": "number", "required": True},
            {"key": "net_mismatch", "label": "Net Mismatch (Cr)", "type": "number", "required": False},
            {"key": "bucket_1_30", "label": "1-30 Day Bucket (Cr)", "type": "number", "required": False},
            {"key": "bucket_31_90", "label": "31-90 Day Bucket (Cr)", "type": "number", "required": False},
            {"key": "bucket_91_180", "label": "91-180 Day Bucket (Cr)", "type": "number", "required": False},
            {"key": "bucket_181_365", "label": "181-365 Day Bucket (Cr)", "type": "number", "required": False},
            {"key": "bucket_above_365", "label": ">365 Day Bucket (Cr)", "type": "number", "required": False},
            {"key": "interest_rate_sensitivity", "label": "Interest Rate Sensitivity", "type": "text", "required": False},
            {"key": "cumulative_gap_ratio", "label": "Cumulative Gap Ratio (%)", "type": "number", "required": False},
        ],
    },
    "SHAREHOLDING_PATTERN": {
        "name": "Shareholding Pattern",
        "fields": [
            {"key": "quarter", "label": "Quarter / Date", "type": "text", "required": True},
            {"key": "promoter_holding_pct", "label": "Promoter Holding (%)", "type": "number", "required": True},
            {"key": "promoter_pledge_pct", "label": "Promoter Pledge (%)", "type": "number", "required": False},
            {"key": "fii_holding_pct", "label": "FII Holding (%)", "type": "number", "required": False},
            {"key": "dii_holding_pct", "label": "DII Holding (%)", "type": "number", "required": False},
            {"key": "public_holding_pct", "label": "Public Holding (%)", "type": "number", "required": False},
            {"key": "total_shares", "label": "Total Shares", "type": "number", "required": False},
            {"key": "top_10_shareholders", "label": "Top 10 Shareholders", "type": "text", "required": False},
        ],
    },
    "BORROWING_PROFILE": {
        "name": "Borrowing Profile",
        "fields": [
            {"key": "total_borrowings_cr", "label": "Total Borrowings (Cr)", "type": "number", "required": True},
            {"key": "secured_loans_cr", "label": "Secured Loans (Cr)", "type": "number", "required": False},
            {"key": "unsecured_loans_cr", "label": "Unsecured Loans (Cr)", "type": "number", "required": False},
            {"key": "short_term_cr", "label": "Short-term Debt (Cr)", "type": "number", "required": False},
            {"key": "long_term_cr", "label": "Long-term Debt (Cr)", "type": "number", "required": False},
            {"key": "working_capital_cr", "label": "Working Capital (Cr)", "type": "number", "required": False},
            {"key": "consortium_banks", "label": "Consortium Banks", "type": "text", "required": False},
            {"key": "lead_bank", "label": "Lead Bank", "type": "text", "required": False},
            {"key": "avg_interest_rate_pct", "label": "Avg Interest Rate (%)", "type": "number", "required": False},
            {"key": "debt_equity_ratio", "label": "Debt-Equity Ratio", "type": "number", "required": False},
            {"key": "repayment_schedule", "label": "Repayment Schedule / Notes", "type": "text", "required": False},
        ],
    },
    "ANNUAL_REPORT": {
        "name": "Annual Report — Financials",
        "fields": [
            {"key": "financial_year", "label": "Financial Year", "type": "text", "required": True},
            {"key": "revenue_cr", "label": "Revenue (Cr)", "type": "number", "required": True},
            {"key": "operating_profit_cr", "label": "Operating Profit / EBITDA (Cr)", "type": "number", "required": True},
            {"key": "pat_cr", "label": "Profit After Tax (Cr)", "type": "number", "required": True},
            {"key": "total_assets_cr", "label": "Total Assets (Cr)", "type": "number", "required": False},
            {"key": "net_worth_cr", "label": "Net Worth (Cr)", "type": "number", "required": False},
            {"key": "total_debt_cr", "label": "Total Debt (Cr)", "type": "number", "required": False},
            {"key": "cash_from_operations_cr", "label": "Cash from Operations (Cr)", "type": "number", "required": False},
            {"key": "eps", "label": "EPS (₹)", "type": "number", "required": False},
            {"key": "auditor_opinion", "label": "Auditor Opinion", "type": "text", "required": False},
            {"key": "contingent_liabilities_cr", "label": "Contingent Liabilities (Cr)", "type": "number", "required": False},
            {"key": "related_party_transactions", "label": "Related-Party Transactions", "type": "text", "required": False},
        ],
    },
    "PORTFOLIO_DATA": {
        "name": "Portfolio Cuts / Performance Data",
        "fields": [
            {"key": "reporting_date", "label": "Reporting Date", "type": "date", "required": True},
            {"key": "total_portfolio_cr", "label": "Total Portfolio (Cr)", "type": "number", "required": True},
            {"key": "gross_npa_pct", "label": "Gross NPA (%)", "type": "number", "required": False},
            {"key": "net_npa_pct", "label": "Net NPA (%)", "type": "number", "required": False},
            {"key": "provision_coverage_pct", "label": "Provision Coverage (%)", "type": "number", "required": False},
            {"key": "standard_assets_pct", "label": "Standard Assets (%)", "type": "number", "required": False},
            {"key": "sma1_pct", "label": "SMA-1 (%)", "type": "number", "required": False},
            {"key": "sma2_pct", "label": "SMA-2 (%)", "type": "number", "required": False},
            {"key": "top_sectors", "label": "Top Sector-wise Exposure", "type": "text", "required": False},
            {"key": "concentration_top10_pct", "label": "Top 10 Concentration (%)", "type": "number", "required": False},
        ],
    },
    "BANK_STATEMENT": {
        "name": "Bank Statement",
        "fields": [
            {"key": "account_number", "label": "Account Number", "type": "text", "required": True},
            {"key": "bank_name", "label": "Bank Name", "type": "text", "required": True},
            {"key": "period_from", "label": "Period From", "type": "date", "required": False},
            {"key": "period_to", "label": "Period To", "type": "date", "required": False},
            {"key": "opening_balance", "label": "Opening Balance (₹)", "type": "number", "required": False},
            {"key": "closing_balance", "label": "Closing Balance (₹)", "type": "number", "required": False},
            {"key": "total_credits", "label": "Total Credits (₹)", "type": "number", "required": False},
            {"key": "total_debits", "label": "Total Debits (₹)", "type": "number", "required": False},
            {"key": "avg_monthly_balance", "label": "Avg Monthly Balance (₹)", "type": "number", "required": False},
        ],
    },
    "GST_RETURN": {
        "name": "GST Return",
        "fields": [
            {"key": "gstin", "label": "GSTIN", "type": "text", "required": True},
            {"key": "return_period", "label": "Return Period", "type": "text", "required": True},
            {"key": "total_turnover", "label": "Total Turnover (₹)", "type": "number", "required": False},
            {"key": "taxable_value", "label": "Taxable Value (₹)", "type": "number", "required": False},
            {"key": "igst", "label": "IGST (₹)", "type": "number", "required": False},
            {"key": "cgst", "label": "CGST (₹)", "type": "number", "required": False},
            {"key": "sgst", "label": "SGST (₹)", "type": "number", "required": False},
            {"key": "input_tax_credit", "label": "Input Tax Credit (₹)", "type": "number", "required": False},
        ],
    },
    "ITR": {
        "name": "Income Tax Return",
        "fields": [
            {"key": "pan", "label": "PAN", "type": "text", "required": True},
            {"key": "assessment_year", "label": "Assessment Year", "type": "text", "required": True},
            {"key": "total_income", "label": "Total Income (₹)", "type": "number", "required": False},
            {"key": "tax_payable", "label": "Tax Payable (₹)", "type": "number", "required": False},
            {"key": "business_income", "label": "Business Income (₹)", "type": "number", "required": False},
            {"key": "depreciation", "label": "Depreciation (₹)", "type": "number", "required": False},
        ],
    },
    "BALANCE_SHEET": {
        "name": "Balance Sheet",
        "fields": [
            {"key": "as_at_date", "label": "As At Date", "type": "date", "required": True},
            {"key": "total_assets_cr", "label": "Total Assets (Cr)", "type": "number", "required": True},
            {"key": "total_equity_cr", "label": "Total Equity (Cr)", "type": "number", "required": False},
            {"key": "total_liabilities_cr", "label": "Total Liabilities (Cr)", "type": "number", "required": False},
            {"key": "current_assets_cr", "label": "Current Assets (Cr)", "type": "number", "required": False},
            {"key": "non_current_assets_cr", "label": "Non-Current Assets (Cr)", "type": "number", "required": False},
            {"key": "current_liabilities_cr", "label": "Current Liabilities (Cr)", "type": "number", "required": False},
            {"key": "reserves_surplus_cr", "label": "Reserves & Surplus (Cr)", "type": "number", "required": False},
        ],
    },
    "OTHER": {
        "name": "General / Other Document",
        "fields": [
            {"key": "title", "label": "Document Title", "type": "text", "required": False},
            {"key": "summary", "label": "Summary", "type": "text", "required": False},
            {"key": "key_figures", "label": "Key Figures", "type": "text", "required": False},
        ],
    },
}


# ───────────────────────── Pydantic request models ─────────────────────────

class ReviewClassificationRequest(BaseModel):
    action: str  # "approve" | "edit"
    corrected_type: Optional[str] = None  # required when action == "edit"

class SchemaFieldDef(BaseModel):
    key: str
    label: str
    type: str = "text"  # text | number | date
    required: bool = False

class CreateSchemaRequest(BaseModel):
    document_type: str
    schema_name: str
    fields: List[SchemaFieldDef]

class UpdateSchemaRequest(BaseModel):
    schema_name: Optional[str] = None
    fields: Optional[List[SchemaFieldDef]] = None

class ExtractRequest(BaseModel):
    schema_id: Optional[str] = None  # use a saved schema  (or default)

class FieldEditRequest(BaseModel):
    extracted_fields: dict


# ───────────────────────── 1. Classification review ─────────────────────────

@router.get("/documents/{application_id}")
async def get_extraction_documents(application_id: str, db: Session = Depends(get_db)):
    """List all documents with classification & extraction status."""
    docs = (
        db.query(UploadedDocument)
        .filter(UploadedDocument.application_id == application_id)
        .order_by(UploadedDocument.uploaded_at.desc())
        .all()
    )
    return {
        "application_id": application_id,
        "documents": [
            {
                "file_id": d.id,
                "filename": d.original_filename,
                "document_type": d.document_type,
                "classification_confidence": d.classification_confidence,
                "reviewed": d.reviewed or "pending",
                "reviewed_type": d.reviewed_type,
                "effective_type": d.reviewed_type or (d.document_type.value if hasattr(d.document_type, 'value') else d.document_type),
                "parse_status": d.parse_status.value if hasattr(d.parse_status, 'value') else d.parse_status,
                "extraction_schema_id": d.extraction_schema_id,
                "extracted_fields": json.loads(d.extracted_fields_json) if d.extracted_fields_json else None,
                "parsed_data": json.loads(d.parsed_data) if d.parsed_data else None,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            }
            for d in docs
        ],
    }


@router.put("/documents/{document_id}/review")
async def review_classification(
    document_id: str,
    body: ReviewClassificationRequest,
    db: Session = Depends(get_db),
):
    """Approve or edit the auto-classification of a document."""
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    if body.action == "approve":
        doc.reviewed = "approved"
        doc.reviewed_type = None
    elif body.action == "edit":
        if not body.corrected_type:
            raise HTTPException(400, "corrected_type is required when action is 'edit'")
        valid = [e.value for e in DocumentType]
        if body.corrected_type not in valid:
            raise HTTPException(400, f"Invalid type. Must be one of: {valid}")
        doc.reviewed = "edited"
        doc.reviewed_type = body.corrected_type
    else:
        raise HTTPException(400, "action must be 'approve' or 'edit'")

    db.commit()
    eff_type = doc.reviewed_type or (doc.document_type.value if hasattr(doc.document_type, 'value') else doc.document_type)
    return {"file_id": doc.id, "reviewed": doc.reviewed, "effective_type": eff_type}


# ───────────────────────── 2. Schema CRUD ─────────────────────────

@router.get("/schemas/defaults")
async def get_default_schemas():
    """Return all built-in default schemas."""
    return {doc_type: schema for doc_type, schema in DEFAULT_SCHEMAS.items()}


@router.get("/schemas/{application_id}")
async def list_schemas(application_id: str, db: Session = Depends(get_db)):
    """List all user-defined schemas for an application."""
    schemas = (
        db.query(ExtractionSchema)
        .filter(ExtractionSchema.application_id == application_id)
        .order_by(ExtractionSchema.created_at.desc())
        .all()
    )
    return {
        "application_id": application_id,
        "schemas": [
            {
                "id": s.id,
                "document_type": s.document_type,
                "schema_name": s.schema_name,
                "fields": json.loads(s.fields_json),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in schemas
        ],
    }


@router.post("/schemas/{application_id}")
async def create_schema(application_id: str, body: CreateSchemaRequest, db: Session = Depends(get_db)):
    """Create a custom extraction schema."""
    schema = ExtractionSchema(
        id=str(uuid.uuid4()),
        application_id=application_id,
        document_type=body.document_type,
        schema_name=body.schema_name,
        fields_json=json.dumps([f.dict() for f in body.fields]),
    )
    db.add(schema)
    db.commit()
    return {
        "id": schema.id,
        "document_type": schema.document_type,
        "schema_name": schema.schema_name,
        "fields": json.loads(schema.fields_json),
    }


@router.put("/schemas/{schema_id}")
async def update_schema(schema_id: str, body: UpdateSchemaRequest, db: Session = Depends(get_db)):
    """Update a custom extraction schema."""
    schema = db.query(ExtractionSchema).filter(ExtractionSchema.id == schema_id).first()
    if not schema:
        raise HTTPException(404, "Schema not found")
    if body.schema_name is not None:
        schema.schema_name = body.schema_name
    if body.fields is not None:
        schema.fields_json = json.dumps([f.dict() for f in body.fields])
    schema.updated_at = datetime.utcnow()
    db.commit()
    return {"id": schema.id, "schema_name": schema.schema_name, "fields": json.loads(schema.fields_json)}


@router.delete("/schemas/{schema_id}")
async def delete_schema(schema_id: str, db: Session = Depends(get_db)):
    """Delete a custom extraction schema."""
    schema = db.query(ExtractionSchema).filter(ExtractionSchema.id == schema_id).first()
    if not schema:
        raise HTTPException(404, "Schema not found")
    db.delete(schema)
    db.commit()
    return {"deleted": True, "id": schema_id}


# ───────────────────────── 3. Extraction ─────────────────────────

@router.post("/extract/{document_id}")
async def extract_to_schema(document_id: str, body: ExtractRequest, db: Session = Depends(get_db)):
    """
    Run extraction on a document using a schema (custom or default).
    Uses the document's parsed_data and maps it onto the schema fields.
    """
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Determine effective type
    eff_type = doc.reviewed_type or (doc.document_type.value if hasattr(doc.document_type, 'value') else doc.document_type)

    # Resolve schema fields
    if body.schema_id:
        schema = db.query(ExtractionSchema).filter(ExtractionSchema.id == body.schema_id).first()
        if not schema:
            raise HTTPException(404, "Schema not found")
        fields = json.loads(schema.fields_json)
        doc.extraction_schema_id = schema.id
    else:
        default = DEFAULT_SCHEMAS.get(eff_type, DEFAULT_SCHEMAS["OTHER"])
        fields = default["fields"]

    # Build extracted fields from parsed_data
    parsed = json.loads(doc.parsed_data) if doc.parsed_data else {}
    extracted = _map_parsed_to_schema(parsed, fields)

    doc.extracted_fields_json = json.dumps(extracted)
    db.commit()

    return {
        "file_id": doc.id,
        "effective_type": eff_type,
        "schema_fields": fields,
        "extracted": extracted,
    }


@router.put("/extract/{document_id}/fields")
async def update_extracted_fields(document_id: str, body: FieldEditRequest, db: Session = Depends(get_db)):
    """Let the user manually edit the extracted field values."""
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.extracted_fields_json = json.dumps(body.extracted_fields)
    db.commit()
    return {"file_id": doc.id, "extracted_fields": body.extracted_fields}


# ───────────────────────── Helpers ─────────────────────────

def _map_parsed_to_schema(parsed: dict, fields: list) -> dict:
    """
    Best-effort mapping from the free-form parsed_data dict onto the schema fields.
    Walks nested dicts and tries exact key match, then fuzzy substring match.
    """
    flat = _flatten(parsed)
    result = {}
    for f in fields:
        key = f["key"]
        # Exact match
        if key in flat:
            result[key] = flat[key]
            continue
        # Fuzzy: look for the key as a substring in flat keys
        match_val = None
        for pk, pv in flat.items():
            if key.replace("_", " ") in pk.replace("_", " ").lower():
                match_val = pv
                break
        result[key] = match_val if match_val is not None else None
    return result


def _flatten(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten a nested dict."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(_flatten(v, new_key, sep=sep))
        else:
            items[new_key] = v
            items[k] = v  # also store leaf key for easy matching
    return items
