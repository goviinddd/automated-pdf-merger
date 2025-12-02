Automated PDF Merger V1.2 (YOLO + Gemini)

This tool scans input folders for Purchase Orders, Delivery Notes, and Invoices. It detects the PO Number using AI, groups related documents, and merges them into a single PDF.

1. Installation

Install Python 3.10 or higher.

Open a terminal in this folder.

Create a virtual environment:

python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows


Install dependencies:

pip install -r requirements.txt


2. Configuration

Create a .env file in the root directory.

Add your Gemini API key :

GEMINI_API_KEY=your_api_key_here


3. How to Run

Start the system:

python cli.py


Note: On the first run, it will automatically create the input folders (Purchase_order, etc).

Place your PDF files into the newly created input folders.

The system will process them and output files to Merged_PDFs.
