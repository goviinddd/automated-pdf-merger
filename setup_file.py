import os
import pathlib

def create_project_structure():
    root_dir = "pdf_merger"
    
    # 1. Define the directory structure (Folders)
    directories = [
        # Root and Input/Output Folders [cite: 98]
        f"{root_dir}/Purchase_order",
        f"{root_dir}/Delivery_note",
        f"{root_dir}/Sales_invoice",
        f"{root_dir}/Merged_PDFs",
        
        # Source Code Structure [cite: 32-52]
        f"{root_dir}/src",
        f"{root_dir}/src/core",
        f"{root_dir}/src/extractors",
        f"{root_dir}/src/extractors/po_finder",
        f"{root_dir}/src/extractors/text_extractors",
    ]

    # 2. Define the files and their initial content
    files = {
        # Root Config Files
        f"{root_dir}/.env": "# Environment variables\nDB_PATH=merger_state.db\n",
        f"{root_dir}/cli.py": "# Entry point for the CLI [cite: 31]\n",
        f"{root_dir}/requirements.txt": (
            "pdfplumber\n"      # [cite: 19]
            "pytesseract\n"     # [cite: 20]
            "pdf2image\n"       # [cite: 20]
            "pypdf\n"           # [cite: 21]
            "python-dotenv\n"   # [cite: 22]
            "black\n"           # [cite: 24]
            "ruff\n"            # [cite: 24]
        ),

        # SRC Root
        f"{root_dir}/src/__init__.py": "",

        # Core Package [cite: 34-39]
        f"{root_dir}/src/core/__init__.py": "",
        f"{root_dir}/src/core/pipeline.py": "# The Main Orchestrator [cite: 36]\n",
        f"{root_dir}/src/core/database.py": "# The Database Layer [cite: 38]\n",
        f"{root_dir}/src/core/file_utils.py": "# The File System Layer [cite: 39]\n",

        # Extractors Package [cite: 40-44]
        f"{root_dir}/src/extractors/__init__.py": "# The Toolbox Manager [cite: 41]\n",
        f"{root_dir}/src/extractors/base.py": "# The Tool Blueprint (Extractor Interface) [cite: 42]\n",
        f"{root_dir}/src/extractors/models.py": "# The Data Contracts (DocumentInfo) [cite: 44]\n",

        # PO Finder Package [cite: 46-48]
        f"{root_dir}/src/extractors/po_finder/__init__.py": "",
        f"{root_dir}/src/extractors/po_finder/heuristics.py": "# The Regex Engine for finding PO numbers [cite: 48]\n",

        # Text Extractors Package [cite: 49-52]
        f"{root_dir}/src/extractors/text_extractors/__init__.py": "",
        f"{root_dir}/src/extractors/text_extractors/digital.py": "# Tool 1: Pdfplumber Extractor [cite: 51]\n",
        f"{root_dir}/src/extractors/text_extractors/ocr.py": "# Tool 2: Tesseract Extractor [cite: 52]\n",
    }

    # 3. Create Directories
    print(f"Creating project root at: {os.path.abspath(root_dir)}")
    for d in directories:
        os.makedirs(d, exist_ok=True)
        print(f"  [DIR]  {d}")

    # 4. Create Files
    for file_path, content in files.items():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [FILE] {file_path}")

    print("\n✅ Structure created successfully based on Project Blueprint V1.0")
    print("Next Steps:")
    print(f"  1. cd {root_dir}")
    print("  2. pip install -r requirements.txt")

if __name__ == "__main__":
    create_project_structure()