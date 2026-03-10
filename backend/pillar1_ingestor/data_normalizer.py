"""
Data Normalizer - Unifies parsed data from all document sources into a standard financial dataset.
Reads actual parsed data from the database (not hardcoded).
"""
from typing import Dict, Any, Optional, List
import json


class DataNormalizer:
    """
    Normalizes parsed data from Bank Statements, GST Returns, ITR, and Annual Reports
    into a unified financial dataset for cross-verification.
    
    All monetary values are standardized to Indian Crores (Cr).
    """

    def normalize(self, parsed_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes list of parsed document records (from DB) and returns unified dataset.
        
        Args:
            parsed_documents: List of dicts with keys:
                - document_type: str (BANK_STATEMENT, GST_RETURN, ITR, ANNUAL_REPORT)
                - parsed_data: dict (actual parsed output from each parser)
        
        Returns:
            Unified financial dataset with sections: gst, bank, itr, annual_report
        """
        unified = {
            "gst": self._empty_gst(),
            "bank": self._empty_bank(),
            "itr": self._empty_itr(),
            "annual_report": self._empty_annual_report(),
            "sources_available": [],
        }

        for doc in parsed_documents:
            doc_type = doc.get("document_type", "")
            raw = doc.get("parsed_data")
            if raw is None:
                continue
            # parsed_data may be a JSON string from DB
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    continue

            if doc_type == "BANK_STATEMENT":
                unified["bank"] = self._normalize_bank(raw)
                unified["sources_available"].append("bank")
            elif doc_type == "GST_RETURN":
                unified["gst"] = self._normalize_gst(raw)
                unified["sources_available"].append("gst")
            elif doc_type == "ITR":
                unified["itr"] = self._normalize_itr(raw)
                unified["sources_available"].append("itr")
            elif doc_type == "ANNUAL_REPORT":
                unified["annual_report"] = self._normalize_annual_report(raw)
                unified["sources_available"].append("annual_report")

        return unified

    # ── GST ──────────────────────────────────────────────────────────────
    def _normalize_gst(self, data: Dict) -> Dict[str, Any]:
        return {
            "sales_cr": _safe_float(data.get("gstr_1_sales_cr", 0)),
            "sales_3b_cr": _safe_float(data.get("gstr_3b_sales_cr", 0)),
            "purchases_cr": _safe_float(data.get("gstr_2a_purchases_cr", 0)),
            "net_tax_liability_cr": _safe_float(data.get("net_tax_liability_cr", 0)),
            "input_tax_credit_cr": _safe_float(data.get("input_tax_credit_cr", 0)),
            "filing_frequency": data.get("filing_frequency", "Unknown"),
            "trading_partners": data.get("trading_partners", []),
        }

    def _empty_gst(self) -> Dict[str, Any]:
        return {"sales_cr": 0, "sales_3b_cr": 0, "purchases_cr": 0,
                "net_tax_liability_cr": 0, "input_tax_credit_cr": 0,
                "filing_frequency": "Unknown", "trading_partners": []}

    # ── Bank ─────────────────────────────────────────────────────────────
    def _normalize_bank(self, data: Dict) -> Dict[str, Any]:
        cash_flow = data.get("cash_flow_pattern", {})
        return {
            "total_inflows_cr": _safe_float(data.get("total_inflows_cr", 0)),
            "total_outflows_cr": _safe_float(data.get("total_outflows_cr", 0)),
            "avg_monthly_balance_cr": _safe_float(data.get("average_monthly_balance_cr", 0)),
            "num_transactions": int(data.get("number_of_transactions", 0)),
            "bounced_checks": int(data.get("bounced_checks", 0)),
            "overdraft_instances": int(data.get("overdraft_instances", 0)),
            "largest_inflow_cr": _safe_float(data.get("largest_inflow_cr", 0)),
            "largest_outflow_cr": _safe_float(data.get("largest_outflow_cr", 0)),
            "monthly_variability": _safe_float(cash_flow.get("monthly_variability", 0)),
            "inflow_regularity": cash_flow.get("inflow_regularity", "Unknown"),
            "payment_discipline": cash_flow.get("payment_discipline", "Unknown"),
            "counterparty_transactions": data.get("counterparty_transactions", []),
        }

    def _empty_bank(self) -> Dict[str, Any]:
        return {"total_inflows_cr": 0, "total_outflows_cr": 0, "avg_monthly_balance_cr": 0,
                "num_transactions": 0, "bounced_checks": 0, "overdraft_instances": 0,
                "largest_inflow_cr": 0, "largest_outflow_cr": 0,
                "monthly_variability": 0, "inflow_regularity": "Unknown",
                "payment_discipline": "Unknown", "counterparty_transactions": []}

    # ── ITR ──────────────────────────────────────────────────────────────
    def _normalize_itr(self, data: Dict) -> Dict[str, Any]:
        gross = _safe_float(data.get("gross_total_income", 0))
        # ITR amounts may be in rupees – convert to crores
        if gross > 1_000_000:  # likely in rupees
            gross_cr = gross / 1e7
            taxable_cr = _safe_float(data.get("taxable_income", 0)) / 1e7
            tax_paid_cr = _safe_float(data.get("total_tax_paid", 0)) / 1e7
        else:
            gross_cr = gross
            taxable_cr = _safe_float(data.get("taxable_income", 0))
            tax_paid_cr = _safe_float(data.get("total_tax_paid", 0))

        return {
            "revenue_cr": gross_cr,
            "taxable_income_cr": taxable_cr,
            "tax_paid_cr": tax_paid_cr,
            "assessment_year": data.get("assessment_year", "Unknown"),
        }

    def _empty_itr(self) -> Dict[str, Any]:
        return {"revenue_cr": 0, "taxable_income_cr": 0, "tax_paid_cr": 0,
                "assessment_year": "Unknown"}

    # ── Annual Report ────────────────────────────────────────────────────
    def _normalize_annual_report(self, data: Dict) -> Dict[str, Any]:
        return {
            "company_name": data.get("company_name", "Unknown"),
            "financial_year": data.get("financial_year", "Unknown"),
            "revenue_cr": _safe_float(data.get("revenue_cr", 0)),
            "net_profit_cr": _safe_float(data.get("net_profit_cr", 0)),
            "ebitda_cr": _safe_float(data.get("ebitda_cr", 0)),
            "total_debt_cr": _safe_float(data.get("total_debt_cr", 0)),
            "total_equity_cr": _safe_float(data.get("total_equity_cr", 0)),
            "total_assets_cr": _safe_float(data.get("total_assets_cr", 0)),
            "current_assets_cr": _safe_float(data.get("current_assets_cr", 0)),
            "current_liabilities_cr": _safe_float(data.get("current_liabilities_cr", 0)),
            "contingent_liabilities_cr": _safe_float(data.get("contingent_liabilities_cr", 0)),
            "related_party_transactions_cr": _safe_float(data.get("related_party_transactions_cr", 0)),
            "auditor_name": data.get("auditor_name", "Unknown"),
            "auditor_opinion": data.get("auditor_opinion", "Unknown"),
            "pending_litigations": data.get("pending_litigations", []),
        }

    def _empty_annual_report(self) -> Dict[str, Any]:
        return {"company_name": "Unknown", "financial_year": "Unknown",
                "revenue_cr": 0, "net_profit_cr": 0, "ebitda_cr": 0,
                "total_debt_cr": 0, "total_equity_cr": 0, "total_assets_cr": 0,
                "current_assets_cr": 0, "current_liabilities_cr": 0,
                "contingent_liabilities_cr": 0, "related_party_transactions_cr": 0,
                "auditor_name": "Unknown", "auditor_opinion": "Unknown",
                "pending_litigations": []}


def _safe_float(val, default: float = 0.0) -> float:
    """Safely convert to float."""
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default
