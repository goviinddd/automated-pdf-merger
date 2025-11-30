import logging
import numpy as np
from PIL import Image
import pypdfium2 as pdfium 
from ..base import BaseTextExtractor

# Configure logging
logger = logging.getLogger(__name__)

# --- CONSTANTS ---
CONFIDENCE_THRESHOLD = 0.20 

class YoloExtractor(BaseTextExtractor):
    """
    V3.3: High-Precision Mode (YOLO + RapidOCR + Smart Filtering + Early Exit).
    
    - YOLO finds the PO Box.
    - RapidOCR reads the text inside the box.
    - Smart Filter removes non-PO noise.
    - Early Exit: Stops scanning after the first page with a hit (prevents duplicates).
    """
    
    def __init__(self, model_path="po_detector.pt", target_class_id=1):
        self.model_path = model_path
        self.target_class_id = target_class_id
        self.yolo_model = None
        self.ocr_engine = None
        self._loaded = False

    def _load_models(self):
        if self._loaded: return

        # 1. Load YOLO
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(self.model_path)
        except Exception as e:
            logger.warning(f"❌ Could not load YOLO model: {e}")
            return

        # 2. Load RapidOCR (Lightweight)
        try:
            from rapidocr_onnxruntime import RapidOCR
            # Force CPU for stability on low-end devices
            self.ocr_engine = RapidOCR(det_use_cuda=False, cls_use_cuda=False, rec_use_cuda=False)
            logger.info("✅ YOLO + RapidOCR loaded successfully.")
        except ImportError:
            logger.error("RapidOCR not found. Install with: pip install rapidocr_onnxruntime")

        self._loaded = True

    def extract(self, file_path: str) -> str:
        self._load_models()
        if not self.yolo_model or not self.ocr_engine: 
            return ""

        extracted_candidates = []
        try:
            pdf = pdfium.PdfDocument(file_path)
            
            for i in range(len(pdf)):
                page = pdf[i]
                # Render page to image
                pil_image = page.render(scale=3).to_pil().convert("RGB")
                
                # 1. YOLO Scan
                results = self.yolo_model(pil_image, verbose=False, conf=CONFIDENCE_THRESHOLD)
                
                for result in results:
                    for box in result.boxes:
                        # Filter for PO class only
                        if int(box.cls[0]) != self.target_class_id:
                            continue
                        
                        # Crop the detected box
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        # Add a small buffer padding
                        crop = pil_image.crop((x1-5, y1-5, x2+5, y2+5))
                        
                        # 2. RapidOCR on the crop
                        crop_np = np.array(crop)
                        ocr_result, _ = self.ocr_engine(crop_np)
                        
                        if ocr_result:
                            # --- SMART FILTER LOGIC ---
                            # Iterate through every separate line of text found in the box
                            for line in ocr_result:
                                # RapidOCR format: [[[coords], "text", confidence], ...]
                                text_segment = line[1].strip()
                                
                                # Filter A: Length Check (PO numbers are rarely < 4 or > 25 chars)
                                if len(text_segment) > 25 or len(text_segment) < 4:
                                    continue
                                
                                # Filter B: Digit Check 
                                # Must contain at least one digit. Kills "DESCRIPTION", "INVOICE", "QTY"
                                # This ensures we don't grab table headers accidentally.
                                if not any(char.isdigit() for char in text_segment):
                                    continue
                                    
                                extracted_candidates.append(text_segment)

                # --- OPTIMIZATION: EARLY EXIT ---
                # If we found candidates on this page, assume we found the PO and stop.
                # This prevents grabbing the header PO from every single page, 
                # which causes the massive repetition bug.
                if extracted_candidates:
                    logger.debug(f"PO found on page {i+1}. Stopping scan early.")
                    break

            # Return cleaned candidates joined by newline
            return "\n".join(extracted_candidates)

        except Exception as e:
            logger.error(f"Sniper extraction failed for {file_path}: {e}")
            return ""