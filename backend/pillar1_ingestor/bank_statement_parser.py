"""
Bank Statement Parser - Extract transactions and calculate real metrics
"""
import pandas as pd
import pdfplumber
import re
from typing import Dict, List, Any
from datetime import datetime


class BankStatementParser:
    """Parse bank statements and extract financial metrics with real calculations"""
    
    def parse_bank_statement(self, file_path: str) -> Dict[str, Any]:
        """Parse bank statement file"""
        
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return self._parse_excel(file_path)
        elif file_path.endswith('.csv'):
            return self._parse_csv(file_path)
        elif file_path.endswith('.pdf'):
            return self._parse_pdf_statement(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def _parse_excel(self, file_path: str) -> Dict[str, Any]:
        """Parse Excel bank statement with real calculations"""
        try:
            df = pd.read_excel(file_path)
            print(f"   ✓ Loaded Excel with {len(df)} rows")
            return self._calculate_metrics(df)
        except Exception as e:
            print(f"ERROR parsing Excel bank statement: {e}")
            return self._get_default_bank_data()
    
    def _parse_csv(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV bank statement with real calculations"""
        try:
            df = pd.read_csv(file_path)
            print(f"   ✓ Loaded CSV with {len(df)} rows")
            return self._calculate_metrics(df)
        except Exception as e:
            print(f"ERROR parsing CSV bank statement: {e}")
            return self._get_default_bank_data()
    
    def _parse_pdf_statement(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF bank statement using pdfplumber"""
        try:
            print(f"   → Extracting tables from PDF: {file_path}")
            tables = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    table = page.extract_table()
                    if table:
                        tables.extend(table)
            
            if not tables or len(tables) < 2:
                print("   WARNING: No tables found in PDF, returning default data")
                return self._get_default_bank_data()
            
            # First row is usually header
            df = pd.DataFrame(tables[1:], columns=tables[0])
            print(f"   ✓ Extracted {len(df)} transactions from PDF")
            return self._calculate_metrics(df)
            
        except Exception as e:
            print(f"ERROR parsing PDF bank statement: {e}")
            return self._get_default_bank_data()
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate real metrics from bank statement DataFrame
        Detects columns dynamically and computes actual values
        """
        
        # Normalize column names (lowercase, strip spaces)
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Detect important columns (handle various formats)
        debit_col = self._find_column(df, ['debit', 'withdrawal', 'withdraw', 'dr', 'paid out'])
        credit_col = self._find_column(df, ['credit', 'deposit', 'cr', 'received'])
        balance_col = self._find_column(df, ['balance', 'closing balance', 'closing bal'])
        desc_col = self._find_column(df, ['description', 'narration', 'particulars', 'details'])
        date_col = self._find_column(df, ['date', 'transaction date', 'value date', 'txn date'])
        
        if debit_col is None or credit_col is None:
            print("   WARNING: Could not detect debit/credit columns")
            print(f"   Available columns: {df.columns.tolist()}")
            return self._get_default_bank_data()
        
        # Determine if values are already in Crores or full amounts
        # Check for '₹ cr' or 'cr' in column name
        is_already_crores = any(
            'cr' in str(col) and '₹' in str(col) 
            for col in [debit_col, credit_col]
        )
        divisor = 1.0 if is_already_crores else 1e7  # Don't divide if already in Crores
        
        print(f"   → Detected columns: Credit='{credit_col}', Debit='{debit_col}'")
        print(f"   → Values {'are already' if is_already_crores else 'will be converted to'} in Crores")
        
        # Convert to numeric (handle commas, spaces, special characters, ₹ symbol)
        df[debit_col] = pd.to_numeric(
            df[debit_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', '').str.strip(),
            errors='coerce'
        ).fillna(0)
        
        df[credit_col] = pd.to_numeric(
            df[credit_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', '').str.strip(),
            errors='coerce'
        ).fillna(0)
        
        # Calculate totals
        total_inflows = df[credit_col].sum()
        total_outflows = df[debit_col].sum()
        largest_inflow = df[credit_col].max()
        largest_outflow = df[debit_col].max()
        num_transactions = len(df)
        
        # Calculate average balance
        avg_balance = 0.0
        if balance_col:
            df[balance_col] = pd.to_numeric(
                df[balance_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('₹', '').str.strip(),
                errors='coerce'
            )
            avg_balance = df[balance_col].mean()
        
        # Detect overdraft instances
        overdraft_instances = 0
        if balance_col:
            overdraft_instances = int((df[balance_col] < 0).sum())
        
        # Detect bounced cheques
        bounced_count = 0
        if desc_col:
            bounced_count = self.detect_bounced_checks(df, desc_col)
        
        # Detect cash flow pattern
        cash_flow_pattern = self._analyze_cash_flow_pattern(df, credit_col, date_col)
        
        # Extract counterparty transactions from descriptions
        counterparty_transactions = []
        if desc_col:
            counterparty_transactions = self._extract_counterparties(
                df, desc_col, credit_col, debit_col, date_col, divisor
            )
        
        print(f"   ✓ Calculated metrics: Inflows=₹{total_inflows/divisor:.2f}Cr, Outflows=₹{total_outflows/divisor:.2f}Cr")
        if counterparty_transactions:
            unique_parties = set()
            for t in counterparty_transactions:
                for e in (t.get('from_entity',''), t.get('to_entity','')):
                    if e and e != '__APPLICANT__':
                        unique_parties.add(e)
            print(f"   ✓ Extracted {len(counterparty_transactions)} counterparty transactions ({len(unique_parties)} unique entities)")
        
        return {
            'total_inflows_cr': total_inflows / divisor,
            'total_outflows_cr': total_outflows / divisor,
            'average_monthly_balance_cr': avg_balance / divisor,
            'number_of_transactions': num_transactions,
            'bounced_checks': bounced_count,
            'overdraft_instances': overdraft_instances,
            'largest_inflow_cr': largest_inflow / divisor,
            'largest_outflow_cr': largest_outflow / divisor,
            'statement_period_months': 12,
            'cash_flow_pattern': cash_flow_pattern,
            'counterparty_transactions': counterparty_transactions,
        }
    
    def _find_column(self, df: pd.DataFrame, keywords: List[str]) -> str:
        """
        Find column by matching keywords
        Prioritizes exact matches with special characters like '₹ cr'
        """
        # First pass: Look for exact keyword matches (more specific)
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in keywords:
                # Exact match or keyword appears as a whole word
                if keyword == col_lower or f" {keyword} " in f" {col_lower} " or f"({keyword}" in col_lower:
                    return col
        
        # Second pass: Substring match (more lenient)
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in keywords:
                if keyword in col_lower:
                    # Avoid matching 'description' when looking for 'credit'
                    if keyword in ['credit', 'debit'] and 'description' in col_lower:
                        continue
                    return col
        
        return None
    
    def _extract_counterparties(
        self, df: pd.DataFrame, desc_col: str,
        credit_col: str, debit_col: str, date_col: str,
        divisor: float
    ) -> List[Dict[str, Any]]:
        """
        Extract counterparty names from bank statement descriptions.

        Recognises patterns like:
          NEFT from <Company>    → inflow from counterparty
          NEFT to <Company>     → outflow to counterparty
          RTGS from/to <Company>
          IMPS from/to <Company>
          Payment to <Company>
          Receipt from <Company>
          Transfer to/from <Company>
          UPI-<Company>
          BY <Company> / TO <Company>

        Returns list of {from_entity, to_entity, amount, date, description}.
        """
        if desc_col not in df.columns:
            return []

        # Patterns: (direction_keyword, group_for_name, is_inflow)
        # 'from X' means money came IN from X; 'to X' means money went OUT to X
        PATTERNS = [
            # NEFT/RTGS/IMPS from/to
            (re.compile(r'(?:NEFT|RTGS|IMPS|ECS|ACH)\s+from\s+(.+)', re.IGNORECASE), True),
            (re.compile(r'(?:NEFT|RTGS|IMPS|ECS|ACH)\s+to\s+(.+)', re.IGNORECASE), False),
            # Receipt from / Payment to
            (re.compile(r'(?:Receipt|Received|Rcvd|Collection)\s+(?:from\s+)?(.+)', re.IGNORECASE), True),
            (re.compile(r'(?:Payment|Paid)\s+(?:to\s+)?(.+)', re.IGNORECASE), False),
            # Transfer from/to
            (re.compile(r'Transfer\s+from\s+(.+)', re.IGNORECASE), True),
            (re.compile(r'Transfer\s+to\s+(.+)', re.IGNORECASE), False),
            # BY / TO (common in Indian bank statements)
            (re.compile(r'^BY\s+(.+)', re.IGNORECASE), True),
            (re.compile(r'^TO\s+(.+)', re.IGNORECASE), False),
        ]

        # Words that indicate the description is not a counterparty name
        IGNORED = {
            'salary', 'self', 'cash', 'atm', 'interest', 'charges', 'tax',
            'tds', 'gst', 'cheque return', 'insufficient', 'bounce', 'bank',
        }

        transactions: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            desc = str(row.get(desc_col, '')).strip()
            if not desc:
                continue

            desc_lower = desc.lower()
            # Skip non-counterparty rows
            if any(kw in desc_lower for kw in IGNORED):
                continue

            credit_val = float(row.get(credit_col, 0) or 0)
            debit_val = float(row.get(debit_col, 0) or 0)
            amount = max(credit_val, debit_val) / divisor
            if amount <= 0:
                continue

            # Determine if this is an inflow or outflow
            is_inflow = credit_val > debit_val

            counterparty = None
            for pattern, pattern_is_inflow in PATTERNS:
                match = pattern.search(desc)
                if match:
                    counterparty = match.group(1).strip()
                    is_inflow = pattern_is_inflow
                    break

            if not counterparty:
                continue

            # Clean up counterparty name: remove trailing date, ref numbers
            counterparty = re.sub(r'\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-\s]*\d*.*$', '', counterparty, flags=re.IGNORECASE).strip()
            counterparty = re.sub(r'\s*[-/]\s*\d+\s*$', '', counterparty).strip()

            if len(counterparty) < 3:
                continue

            date_val = str(row.get(date_col, '')) if date_col else ''

            transactions.append({
                'from_entity': counterparty if is_inflow else '__APPLICANT__',
                'to_entity': '__APPLICANT__' if is_inflow else counterparty,
                'amount': round(amount, 4),
                'date': date_val,
                'description': desc[:200],
            })

        return transactions
    
    def detect_bounced_checks(self, df: pd.DataFrame, desc_col: str) -> int:
        """
        Detect bounced cheques from description column
        Look for: RETURN, BOUNCE, NSF (Non-Sufficient Funds), CHEQUE RETURN
        """
        if desc_col not in df.columns:
            return 0
        
        bounce_keywords = ['return', 'bounce', 'nsf', 'insufficient', 'dishonor']
        
        count = df[desc_col].astype(str).str.lower().apply(
            lambda x: any(keyword in x for keyword in bounce_keywords)
        ).sum()
        
        return int(count)
    
    def _analyze_cash_flow_pattern(self, df: pd.DataFrame, credit_col: str, date_col: str) -> Dict[str, Any]:
        """
        Analyze cash flow patterns:
        - Inflow regularity (Consistent/Irregular)
        - Monthly variability
        - Payment discipline
        """
        
        try:
            if date_col and date_col in df.columns:
                # Parse dates
                df['parsed_date'] = pd.to_datetime(df[date_col], errors='coerce')
                df_with_dates = df.dropna(subset=['parsed_date'])
                
                if len(df_with_dates) > 0:
                    # Group by month
                    monthly_inflow = df_with_dates.groupby(
                        df_with_dates['parsed_date'].dt.to_period('M')
                    )[credit_col].sum()
                    
                    variability = monthly_inflow.std()
                    mean_inflow = monthly_inflow.mean()
                    
                    # Determine pattern
                    if mean_inflow > 0 and variability < mean_inflow * 0.3:
                        pattern = "Consistent"
                        discipline = "Excellent"
                    elif mean_inflow > 0 and variability < mean_inflow * 0.5:
                        pattern = "Moderate"
                        discipline = "Good"
                    else:
                        pattern = "Irregular"
                        discipline = "Needs Attention"
                    
                    return {
                        'inflow_regularity': pattern,
                        'payment_discipline': discipline,
                        'monthly_variability': float(variability) if variability else 0.0
                    }
        
        except Exception as e:
            print(f"   Warning: Could not analyze cash flow pattern: {e}")
        
        return {
            'inflow_regularity': 'Unknown',
            'payment_discipline': 'Unknown',
            'monthly_variability': 0.0
        }
    
    def _get_default_bank_data(self) -> Dict[str, Any]:
        """Return default bank statement data when parsing fails"""
        return {
            'total_inflows_cr': 0.0,
            'total_outflows_cr': 0.0,
            'average_monthly_balance_cr': 0.0,
            'number_of_transactions': 0,
            'bounced_checks': 0,
            'overdraft_instances': 0,
            'largest_inflow_cr': 0.0,
            'largest_outflow_cr': 0.0,
            'statement_period_months': 12,
            'cash_flow_pattern': {
                'inflow_regularity': 'Unknown',
                'payment_discipline': 'Unknown',
                'monthly_variability': 0.0
            },
            'counterparty_transactions': [],
        }
