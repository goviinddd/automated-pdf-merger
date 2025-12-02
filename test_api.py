import os
import logging
import json
from dotenv import load_dotenv
from pdf2image import convert_from_path
from src.extractors.api_connector import extract_line_items_from_page

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIG ---
# Ensure this matches your actual file
TEST_PDF = "Purchase_order/PO_SIV_RAK_25_2876_Ades_3.pdf" 

def run_test():
    # 1. Check API Key
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        logger.error("❌ GEMINI_API_KEY not found in .env!")
        return
    
    if not os.path.exists(TEST_PDF):
        logger.error(f"❌ File not found: {TEST_PDF}")
        return

    logger.info(f"📄 Processing PDF: {TEST_PDF}")
    
    # 2. Convert PDF to Images (300 DPI for clarity)
    try:
        images = convert_from_path(TEST_PDF, dpi=300)
        logger.info(f"✅ Converted {len(images)} pages.")
    except Exception as e:
        logger.error(f"Failed to convert PDF: {e}")
        return

    # 3. Loop through pages until we find data
    all_items = []
    
    for i, image in enumerate(images):
        page_num = i + 1
        logger.info(f"🔍 Scanning Page {page_num}...")
        
        result_json_str = extract_line_items_from_page(image)
        
        try:
            items = json.loads(result_json_str)
            if items:
                logger.info(f"🎉 FOUND {len(items)} items on Page {page_num}!")
                all_items.extend(items)
                # Uncomment the next line if you want to stop after the first valid page
                # break 
            else:
                logger.info(f"   No items found on Page {page_num}.")
        except json.JSONDecodeError:
            logger.error(f"   Failed to decode JSON from Page {page_num}: {result_json_str}")

    # 4. Final Report
    print("\n" + "="*40)
    print("   FINAL EXTRACTION RESULT   ")
    print("="*40)
    if all_items:
        print(json.dumps(all_items, indent=2))
    else:
        print("❌ No items found in the entire document.")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_test()