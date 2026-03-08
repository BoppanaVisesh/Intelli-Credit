"""
Quick Kaggle Dataset Downloader - Auto mode
Downloads credit datasets without confirmation prompt
"""
from pathlib import Path
import sys

def main():
    print("=" * 70)
    print("📊 DOWNLOADING KAGGLE CREDIT DATASETS")
    print("=" * 70)
    
    # Check Kaggle config
    kaggle_config = Path.home() / '.kaggle' / 'kaggle.json'
    if not kaggle_config.exists():
        print(f"\n❌ Kaggle API key not found at: {kaggle_config}")
        return False
    
    print(f"\n✅ Kaggle configured")
    
    # Import Kaggle API
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("✅ Kaggle API authenticated")
    except Exception as e:
        print(f"❌ Failed to authenticate: {e}")
        return False
    
    # Define datasets (starting with smallest for testing)
    datasets = [
        {
            'name': 'uciml/german-credit',
            'output': 'ml/data/kaggle/german_credit',
            'description': 'German Credit (1K records - quick test)'
        },
        {
            'name': 'laotse/credit-risk-dataset',
            'output': 'ml/data/kaggle/credit_risk',
            'description': 'Credit Risk (32K records)'
        },
        {
            'name': 'yasserh/loan-default-dataset',
            'output': 'ml/data/kaggle/loan_default',
            'description': 'Loan Default (122K+ records)'
        }
    ]
    
    successful = []
    failed = []
    
    for ds in datasets:
        print(f"\n{'='*70}")
        print(f"📦 {ds['description']}")
        print(f"   Dataset: {ds['name']}")
        print(f"{'='*70}")
        
        try:
            # Create output directory
            output_path = Path(ds['output'])
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Download
            print(f"   ⏳ Downloading...")
            api.dataset_download_files(
                ds['name'],
                path=str(output_path),
                unzip=True
            )
            
            # Check files
            csv_files = list(output_path.glob('*.csv'))
            if csv_files:
                print(f"   ✅ SUCCESS! Downloaded {len(csv_files)} file(s)")
                for f in csv_files:
                    size_mb = f.stat().st_size / (1024 * 1024)
                    print(f"      • {f.name} ({size_mb:.1f} MB)")
                successful.append(ds['description'])
            else:
                print(f"   ⚠️  Downloaded but no CSV files found")
                failed.append(ds['description'])
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed.append(ds['description'])
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 DOWNLOAD SUMMARY")
    print(f"{'='*70}")
    print(f"\n✅ Successful: {len(successful)}/{len(datasets)}")
    for ds in successful:
        print(f"   • {ds}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for ds in failed:
            print(f"   • {ds}")
    
    if successful:
        print(f"\n{'='*70}")
        print("🎯 NEXT STEP: RETRAIN MODEL WITH REAL DATA")
        print(f"{'='*70}")
        print("\nRun:")
        print("   python ml/train_model.py")
        print("\nThe model will automatically use the downloaded datasets!")
        return True
    else:
        print("\n⚠️  No datasets downloaded successfully")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
