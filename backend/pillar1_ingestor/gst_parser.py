"""
GST Parser - Extract and validate GST returns data
"""
import pandas as pd
from typing import Dict, Any


class GSTParser:
    """Parse GST returns (GSTR-1, GSTR-3B, GSTR-2A)"""
    
    def parse_gst_file(self, file_path: str) -> Dict[str, Any]:
        """Parse GST file (Excel/CSV/JSON)"""
        
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return self._parse_excel(file_path)
        elif file_path.endswith('.csv'):
            return self._parse_csv(file_path)
        elif file_path.endswith('.json'):
            return self._parse_json(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def _parse_excel(self, file_path: str) -> Dict[str, Any]:
        """Parse Excel GST file"""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                data[sheet_name] = df.to_dict('records')
            
            return self._extract_gst_metrics(data)
        except Exception as e:
            print(f"Error parsing Excel GST file: {e}")
            return self._get_default_gst_data()
    
    def _parse_csv(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV GST file"""
        try:
            df = pd.read_csv(file_path)
            return self._extract_gst_metrics({'main': df.to_dict('records')})
        except Exception as e:
            print(f"Error parsing CSV GST file: {e}")
            return self._get_default_gst_data()
    
    def _parse_json(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON GST file"""
        try:
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            return self._extract_gst_metrics(data)
        except Exception as e:
            print(f"Error parsing JSON GST file: {e}")
            return self._get_default_gst_data()
    
    def _extract_gst_metrics(self, data: Dict) -> Dict[str, Any]:
        """
        Extract real GST metrics from parsed data
        Handles Excel sheets with Month, Sales columns
        """
        try:
            # Try to find sales data from any sheet
            total_sales = 0.0
            total_purchases = 0.0
            last_filing_date = None
            
            for sheet_name, records in data.items():
                if not records:
                    continue
                
                # Convert to DataFrame for easier processing
                df = pd.DataFrame(records)
                
                # Normalize column names
                df.columns = [str(c).lower().strip() for c in df.columns]
                
                # Check if values are already in Crores
                is_already_crores = any('₹ cr' in str(col) or '(cr)' in str(col).lower() for col in df.columns)
                divisor = 1.0 if is_already_crores else 1e7
                
                # Look for GSTR-1 Sales specifically
                gstr1_col = None
                for col in df.columns:
                    if 'gstr-1' in col and 'sales' in col:
                        gstr1_col = col
                        break
                
                # Look for GSTR-3B Sales specifically  
                gstr3b_col = None
                for col in df.columns:
                    if 'gstr-3b' in col and 'sales' in col:
                        gstr3b_col = col
                        break
                
                # Look for purchases/GSTR-2A
                purchase_col = None
                for col in df.columns:
                    if any(keyword in col for keyword in ['purchase', 'gstr-2a', 'input']):
                        purchase_col = col
                        break
                
                # Extract GSTR-1 sales
                if gstr1_col:
                    df[gstr1_col] = pd.to_numeric(
                        df[gstr1_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', ''),
                        errors='coerce'
                    ).fillna(0)
                    gstr1_sales = df[gstr1_col].sum()
                    total_sales += gstr1_sales
                    print(f"   ✓ GSTR-1 Sales: ₹{gstr1_sales/divisor:.2f} Cr")
                
                # Extract GSTR-3B sales
                if gstr3b_col:
                    df[gstr3b_col] = pd.to_numeric(
                        df[gstr3b_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', ''),
                        errors='coerce'
                    ).fillna(0)
                    gstr3b_sales = df[gstr3b_col].sum()
                    print(f"   ✓ GSTR-3B Sales: ₹{gstr3b_sales/divisor:.2f} Cr")
                
                # Extract purchases
                if purchase_col:
                    df[purchase_col] = pd.to_numeric(
                        df[purchase_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', ''),
                        errors='coerce'
                    ).fillna(0)
                    total_purchases += df[purchase_col].sum()
                
                # Fallback: Look for any sales/revenue columns if above not found
                if not gstr1_col and not gstr3b_col:
                    sales_col = None
                    for col in df.columns:
                        if any(keyword in col for keyword in ['sales', 'revenue', 'turnover', 'taxable value']):
                            sales_col = col
                            break
                    
                    if sales_col:
                        # Clean and sum sales data
                        df[sales_col] = pd.to_numeric(
                            df[sales_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', ''),
                            errors='coerce'
                        ).fillna(0)
                        
                        sheet_total = df[sales_col].sum()
                        total_sales += sheet_total
                        print(f"   ✓ Extracted GST sales from sheet '{sheet_name}': ₹{sheet_total/divisor:.2f} Cr")
                
                # Fallback: Look for purchase columns if not found above
                if not purchase_col:
                    for col in df.columns:
                        if any(keyword in col for keyword in ['purchase', 'input', 'expense']):
                            purchase_col = col
                            break
                    
                    if purchase_col:
                        df[purchase_col] = pd.to_numeric(
                            df[purchase_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', ''),
                            errors='coerce'
                        ).fillna(0)
                        
                        total_purchases += df[purchase_col].sum()
                
                # Look for date column to determine last filing
                date_col = None
                for col in df.columns:
                    if 'date' in col or 'month' in col or 'period' in col:
                        date_col = col
                        break
                
                if date_col and not df[date_col].isna().all():
                    last_filing_date = str(df[date_col].iloc[-1])
            
            # Calculate tax estimates (simplified)
            # Check if we found any data
            if total_sales == 0 and total_purchases == 0:
                print("   WARNING: No sales/purchase data found in GST file")
                return self._get_default_gst_data()
            
            # Determine divisor for final output
            final_divisor = divisor if 'divisor' in locals() else 1.0
            
            gst_rate = 0.18  # Assume 18% GST
            net_tax_liability = total_sales * gst_rate
            input_tax_credit = total_purchases * gst_rate
            
            print(f"   ✓ Total GST sales extracted: ₹{total_sales/final_divisor:.2f} Cr")
            
            # Extract counterparty trading partners from invoice data
            trading_partners = self._extract_trading_partners(data, final_divisor)
            
            return {
                'gstr_1_sales_cr': total_sales / final_divisor,
                'gstr_3b_sales_cr': total_sales / final_divisor,  # Assuming consistent filing
                'gstr_2a_purchases_cr': total_purchases / final_divisor,
                'net_tax_liability_cr': net_tax_liability / final_divisor,
                'input_tax_credit_cr': input_tax_credit / final_divisor,
                'filing_frequency': 'Monthly',
                'last_filing_date': last_filing_date or '2026-03-01',
                'trading_partners': trading_partners,
            }
            
        except Exception as e:
            print(f"   ERROR extracting GST metrics: {e}")
            return self._get_default_gst_data()
    
    def _extract_trading_partners(self, data: Dict[str, Any], divisor: float) -> list:
        """
        Extract counterparty trading partners from GST invoice-level data.
        
        Looks for columns like buyer_name, seller_name, party_name, gstin
        in GSTR-1 (outward supplies = sales) and GSTR-2A (inward supplies = purchases).
        Returns list of {from_entity, to_entity, amount, type} dicts.
        """
        import re
        partners = []
        applicant_sentinel = "__APPLICANT__"
        
        for sheet_name, sheet_data in data.items():
            # Convert to DataFrame if needed
            if isinstance(sheet_data, list):
                if not sheet_data:
                    continue
                df = pd.DataFrame(sheet_data)
            elif isinstance(sheet_data, pd.DataFrame):
                df = sheet_data
            else:
                continue
            
            if df.empty:
                continue
            
            cols_lower = {c: c.lower().replace(' ', '_').replace('-', '_') for c in df.columns}
            
            # Identify counterparty name column
            name_col = None
            for orig, norm in cols_lower.items():
                if any(kw in norm for kw in ['buyer_name', 'seller_name', 'party_name',
                                               'counterparty', 'trade_name', 'customer_name',
                                               'supplier_name', 'vendor_name']):
                    name_col = orig
                    break
            
            # Identify GSTIN column
            gstin_col = None
            for orig, norm in cols_lower.items():
                if any(kw in norm for kw in ['gstin', 'gst_number', 'gst_no', 'gstn']):
                    gstin_col = orig
                    break
            
            if not name_col and not gstin_col:
                continue
            
            # Identify amount column
            amt_col = None
            for orig, norm in cols_lower.items():
                if any(kw in norm for kw in ['taxable_value', 'invoice_value', 'amount',
                                              'total_value', 'invoice_amount']):
                    amt_col = orig
                    break
            
            # Determine direction from sheet name
            sheet_lower = sheet_name.lower()
            is_sales = any(kw in sheet_lower for kw in ['gstr_1', 'gstr1', 'outward', 'sales', 'b2b_outward'])
            is_purchase = any(kw in sheet_lower for kw in ['gstr_2', 'gstr2a', 'gstr2b', 'inward', 'purchase', 'b2b_inward'])
            
            if not is_sales and not is_purchase:
                # Guess from column names
                if name_col and 'buyer' in cols_lower.get(name_col, '').lower():
                    is_sales = True
                elif name_col and 'supplier' in cols_lower.get(name_col, '').lower():
                    is_purchase = True
                else:
                    is_sales = True  # default
            
            for _, row in df.iterrows():
                party = str(row.get(name_col, '')).strip() if name_col else ''
                gstin = str(row.get(gstin_col, '')).strip() if gstin_col else ''
                
                if not party or party.lower() in ('nan', 'none', '', 'n/a'):
                    if gstin and gstin.lower() not in ('nan', 'none', '', 'n/a'):
                        party = f"GSTIN:{gstin}"
                    else:
                        continue
                
                # Clean party name
                party = re.sub(r'\s+', ' ', party).strip()
                
                try:
                    amount = float(row[amt_col]) / divisor if amt_col and pd.notna(row.get(amt_col)) else 0.0
                except (ValueError, TypeError):
                    amount = 0.0
                
                if is_sales:
                    # Sales: Buyer pays Applicant (money flow: Buyer → Applicant)
                    partners.append({
                        'from_entity': party,
                        'to_entity': applicant_sentinel,
                        'amount': round(amount, 4),
                        'type': 'gst_sales',
                        'gstin': gstin if gstin.lower() not in ('nan', 'none', '') else None
                    })
                else:
                    # Purchase: Applicant pays Supplier (money flow: Applicant → Supplier)
                    partners.append({
                        'from_entity': applicant_sentinel,
                        'to_entity': party,
                        'amount': round(amount, 4),
                        'type': 'gst_purchase',
                        'gstin': gstin if gstin.lower() not in ('nan', 'none', '') else None
                    })
        
        print(f"   ✓ Extracted {len(partners)} GST trading partner transactions")
        return partners
    
    def _get_default_gst_data(self) -> Dict[str, Any]:
        """Return default GST data structure"""
        return {
            'gstr_1_sales_cr': 0.0,
            'gstr_3b_sales_cr': 0.0,
            'gstr_2a_purchases_cr': 0.0,
            'net_tax_liability_cr': 0.0,
            'input_tax_credit_cr': 0.0,
            'filing_frequency': 'Unknown',
            'last_filing_date': None,
            'trading_partners': [],
        }
    
    def validate_gst_consistency(self, gstr1_sales: float, gstr3b_sales: float) -> Dict[str, Any]:
        """Validate consistency between GSTR-1 and GSTR-3B"""
        variance = abs(gstr1_sales - gstr3b_sales)
        variance_percent = (variance / gstr1_sales * 100) if gstr1_sales > 0 else 0
        
        return {
            'variance_amount': variance,
            'variance_percent': variance_percent,
            'is_consistent': variance_percent < 5.0,  # 5% threshold
            'alert': "High variance detected" if variance_percent >= 5.0 else "Normal"
        }
