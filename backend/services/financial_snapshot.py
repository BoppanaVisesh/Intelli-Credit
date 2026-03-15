from typing import Any, Dict


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _first_positive(*values: Any) -> float:
    for value in values:
        numeric = _safe_float(value)
        if numeric > 0:
            return numeric
    return 0.0


def derive_document_backed_dscr(app, annual: Dict[str, Any], bank: Dict[str, Any]) -> float:
    if getattr(app, "dscr", None) and app.dscr > 0:
        return round(float(app.dscr), 2)

    operating_cash_flow = _first_positive(
        annual.get("cash_from_operations_cr"),
        annual.get("operating_cash_flow_cr"),
        annual.get("ebitda_cr"),
        annual.get("net_profit_cr"),
        (bank.get("total_inflows_cr", 0) or 0) - (bank.get("total_outflows_cr", 0) or 0),
    )
    total_debt = _safe_float(annual.get("total_debt_cr", 0))
    finance_cost = _safe_float(annual.get("finance_cost_cr", 0))
    current_maturities = _safe_float(annual.get("current_maturities_cr", 0))

    debt_service = _first_positive(finance_cost + current_maturities, total_debt * 0.15)
    if operating_cash_flow > 0 and debt_service > 0:
        return round(max(0.25, min(5.0, operating_cash_flow / debt_service)), 2)

    return 1.0


def derive_current_ratio(app, annual: Dict[str, Any]) -> float:
    if getattr(app, "current_ratio", None) and app.current_ratio > 0:
        return round(float(app.current_ratio), 2)

    current_assets = _safe_float(annual.get("current_assets_cr", 0))
    current_liabilities = _safe_float(annual.get("current_liabilities_cr", 0))
    if current_assets > 0 and current_liabilities > 0:
        return round(current_assets / current_liabilities, 2)

    return 1.0


def build_financials(app, normalized: Dict[str, Any]) -> Dict[str, Any]:
    gst = normalized.get("gst", {})
    bank = normalized.get("bank", {})
    annual = normalized.get("annual_report", {})
    shareholding = normalized.get("shareholding", {})
    liquidity = normalized.get("liquidity", {})

    gst_sales = _safe_float(gst.get("sales_cr", 0))
    bank_inflows = _safe_float(bank.get("total_inflows_cr", 0))
    bank_outflows = _safe_float(bank.get("total_outflows_cr", 0))
    ar_debt = _safe_float(annual.get("total_debt_cr", 0))
    ar_equity = _safe_float(annual.get("total_equity_cr", 0))
    ar_revenue = _safe_float(annual.get("revenue_cr", 0))

    gst_variance = abs(gst_sales - bank_inflows) / gst_sales * 100 if gst_sales > 0 else 0
    debt_to_equity = ar_debt / ar_equity if ar_equity > 0 else 1.0

    return {
        "dscr": derive_document_backed_dscr(app, annual, bank),
        "current_ratio": derive_current_ratio(app, annual),
        "requested_limit_cr": _safe_float(getattr(app, "requested_limit_cr", 0)),
        "gst_vs_bank_variance": round(gst_variance, 2),
        "debt_to_equity": round(debt_to_equity, 2),
        "revenue_cr": ar_revenue or gst_sales,
        "gst_sales_cr": gst_sales,
        "gst_3b_sales_cr": _safe_float(gst.get("sales_3b_cr", gst_sales)),
        "bank_inflows_cr": bank_inflows,
        "bank_outflows_cr": bank_outflows,
        "operating_cash_flow_cr": _first_positive(
            annual.get("cash_from_operations_cr"),
            annual.get("operating_cash_flow_cr"),
            bank_inflows - bank_outflows,
            annual.get("ebitda_cr"),
            annual.get("net_profit_cr"),
        ),
        "bounced_cheques": int(bank.get("bounced_cheques", 0) or 0),
        "overdraft_instances": int(bank.get("overdraft_instances", 0) or 0),
        "fixed_assets_cr": _safe_float(annual.get("fixed_assets_cr", 0)),
        "total_assets_cr": _safe_float(annual.get("total_assets_cr", 0)),
        "net_worth_cr": ar_equity,
        "promoter_holding_pct": _safe_float(shareholding.get("promoter_holding_pct", 0)),
        "public_holding_pct": _safe_float(shareholding.get("public_holding_pct", 0)),
        "pledged_holding_pct": _safe_float(shareholding.get("pledged_holding_pct", 0)),
        "top10_borrowings_pct": _safe_float(liquidity.get("top10_borrowings_pct", 0)),
        "significant_counterparty_liabilities_pct": _safe_float(liquidity.get("significant_counterparty_liabilities_pct", 0)),
        "short_term_liabilities_pct_total_liabilities": _safe_float(liquidity.get("short_term_liabilities_pct_total_liabilities", 0)),
        "liquidity_management_note": liquidity.get("liquidity_management_note", ""),
    }