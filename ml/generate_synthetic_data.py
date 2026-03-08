"""
Synthetic Credit Data Generator
Generates realistic corporate credit application data for training ML models
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


class SyntheticCreditDataGenerator:
    """
    Generates synthetic credit data based on Indian corporate lending patterns
    """
    
    def __init__(self):
        self.sectors = [
            'Industrial Manufacturing',
            'IT Services', 
            'Textiles',
            'Pharmaceuticals',
            'Construction',
            'Renewable Energy',
            'Food Processing',
            'Automotive Parts',
            'Chemicals',
            'Retail'
        ]
        
        self.company_prefixes = [
            'Apex', 'Global', 'Premier', 'Sterling', 'Universal', 
            'United', 'National', 'Supreme', 'Elite', 'Prime',
            'Modern', 'Classic', 'Royal', 'Imperial', 'Crown'
        ]
        
        self.company_suffixes = [
            'Industries', 'Manufacturing', 'Enterprises', 'Solutions',
            'Technologies', 'Corporation', 'Group', 'Systems'
        ]
    
    def generate_dataset(self, n_samples: int = 500) -> pd.DataFrame:
        """
        Generate synthetic credit dataset
        
        Args:
            n_samples: Number of applications to generate
            
        Returns:
            DataFrame with features and labels
        """
        
        print(f"Generating {n_samples} synthetic credit applications...")
        
        data = []
        
        for i in range(n_samples):
            # Generate company details
            company_name = f"{random.choice(self.company_prefixes)} {random.choice(self.company_suffixes)}"
            sector = random.choice(self.sectors)
            
            # Generate financial metrics with correlations
            # Good companies cluster
            is_good = random.random() > 0.4  # 60% approval rate
            
            if is_good:
                dscr = np.random.normal(1.5, 0.3)
                current_ratio = np.random.normal(1.8, 0.4)
                debt_to_equity = np.random.normal(1.2, 0.5)
                gst_vs_bank_variance = abs(np.random.normal(2, 1.5))
                circular_trading_risk = np.random.uniform(0, 30)
                litigation_count = np.random.choice([0, 0, 0, 1], p=[0.7, 0.15, 0.1, 0.05])
                promoter_sentiment = random.choices(
                    ['POSITIVE', 'NEUTRAL', 'NEGATIVE'],
                    weights=[0.6, 0.3, 0.1]
                )[0]
                sector_risk = np.random.uniform(10, 40)
            else:
                # Bad companies
                dscr = np.random.normal(0.8, 0.2)
                current_ratio = np.random.normal(1.1, 0.3)
                debt_to_equity = np.random.normal(2.5, 0.8)
                gst_vs_bank_variance = abs(np.random.normal(8, 3))
                circular_trading_risk = np.random.uniform(40, 100)
                litigation_count = np.random.choice([1, 2, 3, 4], p=[0.4, 0.3, 0.2, 0.1])
                promoter_sentiment = random.choices(
                    ['POSITIVE', 'NEUTRAL', 'NEGATIVE'],
                    weights=[0.1, 0.3, 0.6]
                )[0]
                sector_risk = np.random.uniform(40, 80)
            
            # Clip values to realistic ranges
            dscr = max(0.1, min(3.0, dscr))
            current_ratio = max(0.3, min(4.0, current_ratio))
            debt_to_equity = max(0.1, min(5.0, debt_to_equity))
            gst_vs_bank_variance = max(0, min(20, gst_vs_bank_variance))
            
            # Calculate features
            gstr_1_sales = np.random.uniform(10, 200)  # Crores
            bank_inflows = gstr_1_sales * (1 + gst_vs_bank_variance/100 * random.choice([-1, 1]))
            
            requested_limit = gstr_1_sales * np.random.uniform(0.3, 0.8)
            
            # Due diligence notes score
            due_diligence_score = np.random.uniform(0, 5) if is_good else np.random.uniform(-5, 0)
            
            # Calculate final score (rule-based for training data)
            score = 100
            score += (dscr - 1.25) * 30
            score += (current_ratio - 1.5) * 10
            score -= (debt_to_equity - 1.5) * 8
            score -= gst_vs_bank_variance * 1.5
            score -= circular_trading_risk * 0.3
            score -= litigation_count * 12
            
            if promoter_sentiment == 'NEGATIVE':
                score -= 20
            elif promoter_sentiment == 'POSITIVE':
                score += 10
            
            score -= sector_risk * 0.3
            score += due_diligence_score * 2
            
            score = max(0, min(100, score))
            
            # Determine decision
            if score >= 75:
                decision = 'APPROVE'
                actual_default = 0 if random.random() > 0.05 else 1  # 5% default rate
            elif score >= 60:
                decision = 'CONDITIONAL_APPROVE'
                actual_default = 0 if random.random() > 0.15 else 1  # 15% default
            else:
                decision = 'REJECT'
                actual_default = 1 if random.random() > 0.4 else 0  # 60% would default
            
            # Create record
            record = {
                'application_id': f'SYN-{2024+i//100}-{str(i).zfill(5)}',
                'company_name': company_name,
                'sector': sector,
                'requested_limit_cr': round(requested_limit, 2),
                'gstr_1_sales_cr': round(gstr_1_sales, 2),
                'bank_inflows_cr': round(bank_inflows, 2),
                'dscr': round(dscr, 2),
                'current_ratio': round(current_ratio, 2),
                'debt_to_equity': round(debt_to_equity, 2),
                'gst_vs_bank_variance': round(gst_vs_bank_variance, 2),
                'circular_trading_risk_score': round(circular_trading_risk, 2),
                'litigation_count': litigation_count,
                'promoter_sentiment': promoter_sentiment,
                'sector_risk_score': round(sector_risk, 2),
                'due_diligence_score': round(due_diligence_score, 2),
                'final_score': round(score, 2),
                'decision': decision,
                'actual_default': actual_default,
                'timestamp': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
            }
            
            data.append(record)
        
        df = pd.DataFrame(data)
        
        print(f"✅ Generated {len(df)} records")
        print(f"   - Approvals: {len(df[df['decision']=='APPROVE'])} ({len(df[df['decision']=='APPROVE'])/len(df)*100:.1f}%)")
        print(f"   - Conditional: {len(df[df['decision']=='CONDITIONAL_APPROVE'])} ({len(df[df['decision']=='CONDITIONAL_APPROVE'])/len(df)*100:.1f}%)")
        print(f"   - Rejections: {len(df[df['decision']=='REJECT'])} ({len(df[df['decision']=='REJECT'])/len(df)*100:.1f}%)")
        print(f"   - Default Rate: {df['actual_default'].mean()*100:.1f}%")
        
        return df
    
    def save_to_files(self, df: pd.DataFrame, output_dir: str = 'ml/data'):
        """Save generated data to multiple formats"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save as CSV
        csv_path = f'{output_dir}/synthetic_credit_data.csv'
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved CSV: {csv_path}")
        
        # Save as JSON
        json_path = f'{output_dir}/synthetic_credit_data.json'
        df.to_json(json_path, orient='records', indent=2)
        print(f"✅ Saved JSON: {json_path}")
        
        # Save train/test split
        from sklearn.model_selection import train_test_split
        
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
        
        train_path = f'{output_dir}/train_data.csv'
        test_path = f'{output_dir}/test_data.csv'
        
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        print(f"✅ Saved Training: {train_path} ({len(train_df)} samples)")
        print(f"✅ Saved Testing: {test_path} ({len(test_df)} samples)")
        
        return csv_path, json_path, train_path, test_path


def main():
    """Generate synthetic credit data"""
    
    generator = SyntheticCreditDataGenerator()
    
    # Generate 1000 samples
    df = generator.generate_dataset(n_samples=1000)
    
    # Display statistics
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    print(f"\nShape: {df.shape}")
    print(f"\nFeatures: {list(df.columns)}")
    print(f"\nSample Statistics:")
    print(df[['dscr', 'current_ratio', 'debt_to_equity', 'final_score', 'actual_default']].describe())
    
    print(f"\nDecision Distribution:")
    print(df['decision'].value_counts())
    
    print(f"\nSector Distribution:")
    print(df['sector'].value_counts())
    
    # Save files
    print("\n" + "="*60)
    print("SAVING FILES")
    print("="*60 + "\n")
    generator.save_to_files(df)
    
    print("\n" + "="*60)
    print("✅ DATA GENERATION COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review data: ml/data/synthetic_credit_data.csv")
    print("2. Train model: python ml/train_model.py")
    print("3. Test API with real predictions")


if __name__ == "__main__":
    main()
