import os
import shutil
from pathlib import Path

def clean_pycache():
    """Deletes all __pycache__ folders to force Python to reload code."""
    root = Path(".")
    print("🧹 Cleaning __pycache__ files...")
    for p in root.rglob("__pycache__"):
        try:
            shutil.rmtree(p)
            print(f"   Deleted: {p}")
        except Exception as e:
            print(f"   Failed to delete {p}: {e}")

def fix_init_file():
    """Overwrites the problematic __init__.py with the correct content."""
    file_path = Path("src/extractors/text_extractors/__init__.py")
    
    # The CORRECT content (No import of models)
    content = (
        "from .digital import FastDigitalExtractor, AiDigitalExtractor\n"
        "from .ocr import TesseractExtractor\n\n"
        "__all__ = ['FastDigitalExtractor', 'AiDigitalExtractor', 'TesseractExtractor']\n"
    )
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Fixed: {file_path}")
        print("   (Verifying: It does NOT contain 'from .models import DocumentInfo')")
    except Exception as e:
        print(f"❌ Failed to fix {file_path}: {e}")

if __name__ == "__main__":
    clean_pycache()
    fix_init_file()
    print("\n🚀 Repair complete. Please run 'python3 cli.py' again.")