import logging
import numpy as np
from PIL import Image, ImageChops
import pytesseract
import cv2  # Used for local binarization
from pdf2image import convert_from_path
from ..base import BaseTextExtractor
import torch # <-- ADDED TORCH IMPORT

# Configure logging
logger = logging.getLogger(__name__)

# --- CONSTANTS ---
SURYA_TASK_NAME = 'ocr_without_boxes'
CONFIDENCE_THRESHOLD = 0.30

class YoloExtractor(BaseTextExtractor):
    """
    V1.8: Flow Control Fix. Ensures YOLO model is loaded ONLY ONCE before attempts to load Surya.
    """
    
    def __init__(self, model_path="po_detector.pt", target_class_id=1):
        self.model_path = model_path
        self.target_class_id = target_class_id
        self.yolo_model = None
        
        self.surya_predictor = None
        self.det_predictor = None 
        self.use_tesseract_fallback = True
        
        self._loaded = False

    def _preprocess_image(self, pil_image: Image.Image) -> Image.Image:
        # Minimal pre-processing: preserves color/grayscale for YOLO/Surya
        try:
            return pil_image.convert('RGB')
        except Exception as e:
            logger.warning(f"Image format conversion failed: {e}. Using raw image.")
            return pil_image
            
    def _binarize_crop(self, pil_image: Image.Image) -> Image.Image:
        """Helper to binarize a small crop for Tesseract if necessary."""
        try:
            img_array = np.array(pil_image.convert('RGB'))
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return Image.fromarray(binary).convert('L')
        except Exception:
            return pil_image

    def _load_models(self):
        if self._loaded: return

        # 1. Load YOLO (The Spotter) - MUST BE OUTSIDE SURYA BLOCK
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(self.model_path)
            logger.info(f"YOLO Classes detected: {self.yolo_model.names}")
        except Exception as e:
            logger.warning(f"❌ Could not load YOLO model: {e}")
            self.yolo_model = None
            return # EXIT if primary tool fails

        # 2. Try Loading Surya (The AI Reader) - DISABLED FOR SPEED
        # We set use_tesseract_fallback = True in __init__, so we only need to attempt 
        # to load Surya if we want to risk the slowness/crash. We can safely skip the attempt.
        
        # Original block of code related to Surya init has been removed for performance.
        # Ensure we log that we are using the backup.
        if self.use_tesseract_fallback:
             logger.info("Using Tesseract/YOLO fallback for speed.")
        
        self._loaded = True
        
    def _tesseract_spin_cycle(self, crop_image) -> str:
        """
        Backup Strategy: Runs on a binarized version of the crop to boost Tesseract accuracy.
        """
        binarized_crop = self._binarize_crop(crop_image)
        
        attempts = [
            (0, '--psm 7'),    # Normal
            (-90, '--psm 7'),  # Vertical Right
            (90, '--psm 7')    # Vertical Left
        ]

        for angle, config in attempts:
            if angle != 0:
                rotated = binarized_crop.rotate(angle, expand=True)
            else:
                rotated = binarized_crop
            
            text = pytesseract.image_to_string(rotated, lang='eng', config=config)
            clean = text.strip().upper()
            
            if len(clean) >= 6 and sum(c.isdigit() for c in clean) >= 4:
                return clean
        return ""

    def extract(self, file_path: str) -> str:
        self._load_models()
        if not self.yolo_model: 
            return ""

        extracted_texts = []
        try:
            images = convert_from_path(file_path, dpi=300)
            
            for i, image in enumerate(images):
                
                processed_image = self._preprocess_image(image)
                
                # 1. YOLO Scan runs on the cleaner image
                results = self.yolo_model(processed_image, verbose=False, conf=CONFIDENCE_THRESHOLD)
                
                crops = []
                for result in results:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        
                        # PO-ONLY TARGET LOGIC
                        if class_id != self.target_class_id:
                            continue
                        
                        coords = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = map(int, coords)
                        crop = processed_image.crop((x1-5, y1-5, x2+5, y2+5)) 
                        crops.append(crop)
                
                if not crops:
                    continue

                # 2. Recognition Phase
                # Since Surya is explicitly disabled, we always use Tesseract
                for crop in crops:
                    txt = self._tesseract_spin_cycle(crop)
                    if txt: extracted_texts.append(txt)

            return "\n".join(extracted_texts)

        except Exception as e:
            logger.error(f"YOLO extraction failed for {file_path}: {e}")
            return ""