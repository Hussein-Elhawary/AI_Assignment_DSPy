#!/usr/bin/env python3
"""
Environment validation script.
Checks if all required files and dependencies are in place.
"""

import os
import sys


def check_file(filepath, description):
    """Check if a file exists and report status."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ MISSING {description}: {filepath}")
        return False


def check_directory(dirpath, description, min_files=0, extension=None):
    """Check if a directory exists and optionally validate file count."""
    if not os.path.exists(dirpath):
        print(f"✗ MISSING {description}: {dirpath}")
        return False
    
    if not os.path.isdir(dirpath):
        print(f"✗ {description} is not a directory: {dirpath}")
        return False
    
    # Count files with specific extension if provided
    if extension:
        files = [f for f in os.listdir(dirpath) if f.endswith(extension)]
        file_count = len(files)
        
        if file_count >= min_files:
            print(f"✓ {description}: {dirpath} ({file_count} {extension} files)")
            if file_count > 0:
                for f in files:
                    print(f"    - {f}")
            return True
        else:
            print(f"✗ {description}: {dirpath} (found {file_count} {extension} files, need at least {min_files})")
            return False
    else:
        print(f"✓ {description}: {dirpath}")
        return True


def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name.replace('-', '_'))
        print(f"✓ Package installed: {package_name}")
        return True
    except ImportError:
        print(f"✗ MISSING package: {package_name}")
        return False


def main():
    """Run all environment checks."""
    print("=" * 70)
    print("Environment Validation for Retail Analytics AI Agent")
    print("=" * 70)
    
    all_ok = True
    
    # Check core files
    print("\n[1] Checking Core Files...")
    all_ok &= check_file("requirements.txt", "Requirements file")
    all_ok &= check_file("run_agent_hybrid.py", "Main entry point")
    all_ok &= check_file("agent/graph_hybrid.py", "LangGraph implementation")
    all_ok &= check_file("agent/dspy_signatures.py", "DSPy signatures")
    all_ok &= check_file("agent/rag/retrieval.py", "Retrieval module")
    all_ok &= check_file("agent/rag/tools/sqlite_tool.py", "SQLite tool")
    all_ok &= check_file("agent/optimize_refine.py", "Optimization script")
    
    # Check data directory
    print("\n[2] Checking Data Directory...")
    all_ok &= check_file("data/northwind.sqlite", "Northwind database")
    
    # Check docs directory
    print("\n[3] Checking Documentation Directory...")
    docs_ok = check_directory("docs", "Documentation folder", min_files=4, extension=".md")
    all_ok &= docs_ok
    
    if not docs_ok:
        print("    Note: You need at least 4 .md files in the docs/ folder for RAG")
    
    # Check input file
    print("\n[4] Checking Input Files...")
    input_ok = check_file("sample_questions_hybrid_eval.jsonl", "Sample questions file")
    all_ok &= input_ok
    
    if not input_ok:
        print("    Note: Create this file with test questions in JSONL format")
        print("    Example: {\"id\": \"q1\", \"question\": \"...\", \"format_hint\": \"int\"}")
    
    # Check Python packages
    print("\n[5] Checking Python Dependencies...")
    packages = [
        "dspy",
        "langgraph",
        "langchain_core",
        "pydantic",
        "rank_bm25",
        "numpy",
        "pandas",
        "sklearn"
    ]
    
    packages_ok = True
    for pkg in packages:
        pkg_ok = check_python_package(pkg)
        packages_ok &= pkg_ok
        all_ok &= pkg_ok
    
    if not packages_ok:
        print("\n    To install missing packages:")
        print("    pip install -r requirements.txt")
    
    # Check Ollama (optional but recommended)
    print("\n[6] Checking Ollama Setup...")
    import subprocess
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Ollama is installed and accessible")
            if "phi3.5" in result.stdout:
                print("✓ phi3.5 model is available")
            else:
                print("⚠ phi3.5 model not found. Run: ollama pull phi3.5")
                all_ok = False
        else:
            print("⚠ Ollama installed but not responding")
            all_ok = False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Ollama not found or not running")
        print("    Install from: https://ollama.com/download")
        print("    Then run: ollama pull phi3.5")
        all_ok = False
    
    # Check optional optimized model
    print("\n[7] Checking Optional Components...")
    if os.path.exists("agent/sql_gen_optimized.json"):
        print("✓ Optimized SQL Generator found (will be auto-loaded)")
    else:
        print("ℹ Optimized SQL Generator not found (run agent/optimize_refine.py to create)")
    
    # Final summary
    print("\n" + "=" * 70)
    if all_ok:
        print("✓✓✓ Environment is ready! ✓✓✓")
        print("=" * 70)
        print("\nYou can now run:")
        print("  python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out outputs_hybrid.jsonl")
    else:
        print("✗✗✗ Environment has issues - see above ✗✗✗")
        print("=" * 70)
        print("\nPlease fix the missing components before running the agent.")
        sys.exit(1)


if __name__ == "__main__":
    main()
