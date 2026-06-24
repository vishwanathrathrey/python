#!/usr/bin/env python3
"""
Credit Risk ML System - Pipeline Runner
Processes files from interim/ to processed/ using data_processor.py
"""

import subprocess
import sys
import os
import json
from pathlib import Path
import time
import platform

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.absolute()
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
PYSPARK_DIR = PROJECT_ROOT / "pyspark"
SMOKE_TEST_SAMPLE = 0.001

# Create directories
DATA_INTERIM.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Load metadata from interim folder
metadata_path = DATA_INTERIM / "metadata.json"
METADATA = {}
if metadata_path.exists():
    with open(metadata_path, 'r') as f:
        METADATA = json.load(f)
        print("✅ Loaded metadata.json")

# Get files to process
def get_files_to_process():
    """Get list of files from interim directory"""
    files = []
    for parquet_file in sorted(DATA_INTERIM.glob("*_standardized.parquet")):
        if parquet_file.name == "metadata.json":
            continue
        
        size_mb = parquet_file.stat().st_size / (1024**2)
        if size_mb < 50:
            size_category = "small"
        elif size_mb < 300:
            size_category = "medium"
        else:
            size_category = "large"
        
        # Create output name
        output_name = parquet_file.name.replace("_standardized", "_processed")
        
        # Determine file type from metadata
        base_name = parquet_file.name.replace("_standardized.parquet", "")
        file_type = "metadata"
        if base_name in METADATA:
            shape = METADATA[base_name].get('shape', [0, 0])
            if len(shape) == 2 and shape[1] > 10 and 'client_id' in str(METADATA[base_name].get('columns', [])):
                file_type = "feature_matrix"
        
        files.append({
            "input": parquet_file.name,
            "output": output_name,
            "size_mb": round(size_mb, 1),
            "size_category": size_category,
            "type": file_type,
            "base_name": base_name
        })
    
    return files

FILES = get_files_to_process()

# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def print_header(text):
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

def print_info(text):
    print(f" ℹ️  {text}")

def print_success(text):
    print(f" ✅ {text}")

def print_warning(text):
    print(f" ⚠️  {text}")

def print_error(text):
    print(f" ❌ {text}")


def check_files():
    """Check which input files exist in interim folder"""
    print_header("CHECKING INTERIM FILES")
    
    if not FILES:
        print_warning("No standardized parquet files found in interim folder")
        return [], []
    
    print_success(f"Found {len(FILES)} files to process")
    
    # Show summary from metadata
    if METADATA:
        print_info("\n📊 Files to process:")
        for f in FILES:
            icon = "📊" if f['type'] == 'feature_matrix' else "📄"
            print(f"   {icon} {f['input']} ({f['size_mb']} MB) - {f['type']}")
    
    return FILES, []


def check_environment():
    """Check system resources"""
    print_header("CHECKING ENVIRONMENT")
    
    py_version = sys.version_info
    print_info(f"Python: {py_version.major}.{py_version.minor}.{py_version.micro}")
    print_info(f"OS: {platform.system()} {platform.release()}")
    
    try:
        import psutil
        mem = psutil.virtual_memory()
        print_info(f"RAM: {mem.total / (1024**3):.1f} GB total, {mem.available / (1024**3):.1f} GB available")
    except ImportError:
        print_warning("psutil not installed")
    
    return True


# ------------------------------------------------------------
# Main Menu
# ------------------------------------------------------------

def show_menu():
    """Show interactive menu"""
    print_header("CREDIT RISK PIPELINE RUNNER")
    
    print("\n📋 OPTIONS:\n")
    print("   [1] 🚀 Process ALL files (10% sample, fastest)")
    print("   [2] ⚖️  Process ALL files (30% sample, balanced)")
    print("   [3] 🔥 Process ALL files (100% data, full processing)")
    print("   [4] 🎯 Process SINGLE file")
    print("   [5] 🔍 Check environment")
    print("   [6] 🧹 Clean processed data")
    print("   [7] 📊 Show status")
    print("   [8] 🧪 Process ALL files (0.1% sample, smoke test)")
    print("   [0] ❌ Exit\n")
    
    return input("Enter choice (0-8): ").strip()


def run_single_file(
    file_info,
    sample,
    missing_threshold=60,
    ml_mode=False,
    cast_rules_json="",
    dedup_keys="",
    outlier_method="none",
    outlier_columns="",
    outlier_max_columns=300,
):
    """Run data_processor for one file with optional ML-ready preprocessing"""
    processor = PYSPARK_DIR / "data_processor.py"
    
    if not processor.exists():
        print_error(f"data_processor.py not found in {PYSPARK_DIR}")
        return False
    
    # Build command with supported arguments
    cmd = [
        sys.executable, str(processor),
        "--file", file_info["input"],
        "--output", file_info["output"],
        "--sample", str(sample),
        "--missing-threshold", str(missing_threshold),
        "--input-dir", "data/interim",
        "--output-dir", "data/processed"
    ]
    
    # Add ML-ready flags if enabled
    if ml_mode:
        if cast_rules_json:
            cmd.extend(["--cast-rules", cast_rules_json])
        if dedup_keys:
            cmd.extend(["--dedup-keys", dedup_keys])
        if outlier_method != "none":
            cmd.extend(["--outlier-method", outlier_method])
        if outlier_columns:
            cmd.extend(["--outlier-columns", outlier_columns])
        cmd.extend(["--outlier-max-columns", str(outlier_max_columns)])
        # Enable quality and schema contract reports with default naming
        cmd.extend([
            "--quality-report-file", f"data/processed/{file_info['output'].replace('.parquet', '')}_quality_report.json",
            "--schema-contract-file", f"data/processed/{file_info['output'].replace('.parquet', '')}_schema_contract.json"
        ])
    
    print_info(f"\nProcessing: {file_info['input']} -> {file_info['output']}")
    print_info(f"Size: {file_info['size_mb']} MB ({file_info['size_category']})")
    print_info(f"Type: {file_info['type']}")
    
    start = time.time()
    result = subprocess.run(cmd)
    elapsed = (time.time() - start) / 60
    
    if result.returncode == 0:
        print_success(f"Completed in {elapsed:.2f} minutes")
        return True
    else:
        print_error(f"Failed after {elapsed:.2f} minutes")
        return False


def run_all_files(sample, missing_threshold=60, ml_mode=False):
    """Process all available files in sequence with optional ML-ready mode"""
    available, _ = check_files()
    
    if not available:
        print_error("No files to process!")
        return
    
    print_header(f"PROCESSING {len(available)} FILES")
    print_info(f"Sample: {sample*100}% | Missing threshold: {missing_threshold}%")
    if ml_mode:
        print_info("ML-ready mode: enabled (dedup + outlier handling)")
        print_warning("Quality reports and schema contracts will be generated")
    
    # Group by size
    small_files = [f for f in available if f['size_category'] == 'small']
    medium_files = [f for f in available if f['size_category'] == 'medium']
    large_files = [f for f in available if f['size_category'] == 'large']
    
    print_info(f"Small: {len(small_files)} | Medium: {len(medium_files)} | Large: {len(large_files)}")
    
    successful = 0
    failed = []
    
    # Process small to large
    all_files = small_files + medium_files + large_files
    
    for i, file_info in enumerate(all_files, 1):
        print_header(f"FILE {i}/{len(all_files)}: {file_info['input']}")
        
        ml_dedup = "case_id" if ml_mode and file_info["type"] == "feature_matrix" else ""
        ml_outlier = "iqr_cap" if ml_mode and file_info["type"] == "feature_matrix" else "none"
        ml_outlier_max_cols = 0 if ml_mode and file_info["type"] == "feature_matrix" else 300
        
        success = run_single_file(
            file_info,
            sample,
            missing_threshold,
            ml_mode=ml_mode,
            dedup_keys=ml_dedup,
            outlier_method=ml_outlier,
            outlier_columns="auto",
            outlier_max_columns=ml_outlier_max_cols,
        )
        
        if success:
            successful += 1
        else:
            failed.append(file_info["input"])
        
        # Pause between files
        if i < len(all_files):
            pause = 10 if file_info['size_category'] == 'large' else 5
            print_info(f"Pausing {pause} seconds...")
            time.sleep(pause)
    
    # Summary
    print_header("PROCESSING SUMMARY")
    print_success(f"Successfully processed: {successful}/{len(all_files)} files")
    if failed:
        print_error(f"Failed: {failed}")
    
    show_status()


def clean_processed():
    """Delete all processed files"""
    print_header("CLEANING PROCESSED DATA")
    
    parquet_files = list(DATA_PROCESSED.glob("*.parquet"))
    parquet_dirs = list(DATA_PROCESSED.glob("*.parquet/"))
    all_items = parquet_files + parquet_dirs
    
    if not all_items:
        print_info("No processed files found")
        return
    
    print_info(f"Found {len(all_items)} items:")
    for f in all_items:
        if f.is_dir():
            size = sum(p.stat().st_size for p in f.glob("**/*") if p.is_file()) / (1024**2)
            print(f"   - {f.name}/ ({size:.1f} MB)")
        else:
            size = f.stat().st_size / (1024**2)
            print(f"   - {f.name} ({size:.1f} MB)")
    
    confirm = input("\nDelete all? (y/N): ").strip().lower()
    if confirm == 'y':
        import shutil
        for f in all_items:
            if f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()
        print_success("Cleanup complete")


def show_status():
    """Show current processed files"""
    print_header("PROCESSED FILES")
    
    processed = list(DATA_PROCESSED.glob("*.parquet")) + list(DATA_PROCESSED.glob("*.parquet/"))
    
    if processed:
        total_size = 0
        for f in sorted(processed):
            if f.is_dir():
                size = sum(p.stat().st_size for p in f.glob("**/*") if p.is_file()) / (1024**2)
                modified = time.ctime(f.stat().st_mtime)
                print(f"   📁 {f.name}/ ({size:.1f} MB) - {modified}")
            else:
                size = f.stat().st_size / (1024**2)
                modified = time.ctime(f.stat().st_mtime)
                print(f"   📄 {f.name} ({size:.1f} MB) - {modified}")
            total_size += size
        print_info(f"Total: {len(processed)} files, {total_size:.1f} MB")
    else:
        print_warning("No processed files found")
    
    # Show logs
    logs = list(LOGS_DIR.glob("etl_pipeline_*.log")) + list(LOGS_DIR.glob("processor_*.log"))
    if logs:
        latest = max(logs, key=lambda f: f.stat().st_mtime)
        log_size = latest.stat().st_size / (1024**2)
        print_info(f"Latest log: {latest.name} ({log_size:.2f} MB)")
    
    # Show quality reports and schema contracts
    quality_reports = list(DATA_PROCESSED.glob("*_quality_report.json"))
    schema_contracts = list(DATA_PROCESSED.glob("*_schema_contract.json"))
    if quality_reports or schema_contracts:
        print_info(f"ML artifacts: {len(quality_reports)} quality reports, {len(schema_contracts)} schema contracts")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    print("\n" + "🌟"*35)
    print("🌟   CREDIT RISK PIPELINE RUNNER   🌟")
    print("🌟"*35 + "\n")
    
    check_environment()
    
    while True:
        choice = show_menu()
        
        if choice == '0':
            print_info("Exiting...")
            sys.exit(0)
            
        elif choice == '1':
            print_header("MINIMAL SETTINGS (10% sample)")
            confirm = input("\nProceed? (y/N): ").strip().lower()
            if confirm == 'y':
                run_all_files(sample=0.1)
            
        elif choice == '2':
            print_header("BALANCED SETTINGS (30% sample)")
            confirm = input("\nProceed? (y/N): ").strip().lower()
            if confirm == 'y':
                run_all_files(sample=0.3)
            
        elif choice == '3':
            print_header("FULL PROCESSING (100% DATA + ML-READY)")
            total_size = sum(f['size_mb'] for f in FILES)
            print_info(f"Total data size: ~{total_size:.1f} MB")
            print_info("Sample: 100% | Missing threshold: 60%")
            print_success("ML-ready mode: ENABLED")
            print_info("  ✓ Deduplication: enabled for feature matrices")
            print_info("  ✓ Outlier handling: IQR-based capping across all auto-selected numeric feature columns")
            print_info("  ✓ Quality reports: generated for all files")
            print_info("  ✓ Schema contracts: generated for all files")
            print_warning("This will process ALL data and generate ML artifacts - may take time")
            
            confirm = input("\nProceed? (y/N): ").strip().lower()
            if confirm == 'y':
                run_all_files(sample=1.0, ml_mode=True)
            
        elif choice == '4':
            print_header("CUSTOM SINGLE FILE")
            
            if not FILES:
                print_error("No files available")
                continue
            
            print("\nAvailable files:")
            for i, f in enumerate(FILES, 1):
                print(f"   {i}. {f['input']} ({f['size_mb']} MB) - {f['type']}")
            
            try:
                file_idx = int(input("\nSelect file number: ")) - 1
                if file_idx < 0 or file_idx >= len(FILES):
                    print_error("Invalid selection")
                    continue
                
                file_info = FILES[file_idx]
                
                sample = float(input("Sample fraction (0.0-1.0) [1.0]: ") or "1.0")
                missing = float(input("Missing threshold % [60]: ") or "60")
                
                run_single_file(
                    file_info,
                    sample=sample,
                    missing_threshold=missing
                )
                
            except (ValueError, KeyboardInterrupt):
                print_warning("\nCancelled")
            
        elif choice == '5':
            check_environment()
            input("\nPress Enter to continue...")
            
        elif choice == '6':
            clean_processed()
            input("\nPress Enter to continue...")
            
        elif choice == '7':
            show_status()
            input("\nPress Enter to continue...")

        elif choice == '8':
            print_header("SMOKE TEST SETTINGS (0.1% sample)")
            print_info("This is a quick pipeline check to confirm all processed outputs are created")
            confirm = input("\nProceed? (y/N): ").strip().lower()
            if confirm == 'y':
                run_all_files(sample=SMOKE_TEST_SAMPLE)
            
        else:
            print_error("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\nExiting...")
        sys.exit(0)