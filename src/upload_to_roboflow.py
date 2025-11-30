import os
import glob
from roboflow import Roboflow
from pdf2image import convert_from_path

# --- CONFIGURATION ---
API_KEY = "lXolxCESi2hJ3bWo7lOZ"
PROJECT_ID = "po-labelling-hxh6s"  # Check your URL to confirm this!
INPUT_FOLDER = "PO_EXTRACTION" # Or wherever your 400 docs are
# ---------------------

def upload_bulk():
    print(f"🚀 Connecting to Roboflow Project: {PROJECT_ID}...")
    rf = Roboflow(api_key=API_KEY)
    
    # Note: If your project is public, workspace() works. 
    # If private, you might need rf.workspace("your-workspace-name").project(...)
    try:
        project = rf.workspace().project(PROJECT_ID)
    except Exception as e:
        print(f"❌ Error connecting to project: {e}")
        print("Check your Project ID and API Key.")
        return

    # Find all PDFs
    pdf_files = glob.glob(os.path.join(INPUT_FOLDER, "*.pdf"))
    print(f"found {len(pdf_files)} PDFs. Starting processing...")

    count = 0
    for pdf_path in pdf_files:
        try:
            # 1. Convert locally (Much faster/stable than cloud)
            # We only take the first page usually for POs, but you can loop if needed
            images = convert_from_path(pdf_path, dpi=200) # 200 DPI is enough for labeling
            
            for i, image in enumerate(images):
                # Save temp image
                temp_name = f"temp_upload_{count}_{i}.jpg"
                image.save(temp_name, "JPEG", quality=80)
                
                # 2. Upload via API
                print(f"Uploading {os.path.basename(pdf_path)} (Page {i+1})...")
                project.upload(
                    temp_name, 
                    batch_name="batch_upload_v1", 
                    num_retry_uploads=3
                )
                
                # Cleanup
                if os.path.exists(temp_name):
                    os.remove(temp_name)
            
            count += 1
            
        except Exception as e:
            print(f"⚠️ Failed to process {pdf_path}: {e}")

    print(f"\n✅ Upload Complete! Processed {count} documents.")
    print("Go to Roboflow -> Annotate -> Unassigned to start labeling.")

if __name__ == "__main__":
    upload_bulk()