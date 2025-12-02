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

Add your Gemini API key (if using the fallback feature):

GEMINI_API_KEY=your_api_key_here



3. How to Run

Start the system:

python cli.py



Note: On the first run, it will automatically create the input folders (Purchase_order, etc).

Place your PDF files into the newly created input folders.

The system will process them and output files to Merged_PDFs.

4. Project Structure & File Descriptions

cli.py: The main entry point for the application. Run this script to start the processing loop.

po_detector.pt: The custom-trained YOLOv8 model used to visually detect PO Numbers and Tables in the PDFs.

requirements.txt: A list of all Python libraries required to run the project.

src/: The source code folder containing:

core/: The main pipeline logic and database management.

extractors/: Scripts for OCR (RapidOCR), AI (YOLO/Gemini), and text processing.

logic/: Business logic for linking items and reconciling POs against deliveries.

.env: (Create this yourself) Stores your secret API keys configuration.
