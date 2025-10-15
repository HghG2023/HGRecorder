from paddleocr import PaddleOCR
import paddleocr
from scripts.unique_string_generate import unique_name
from scripts.path_control import PM
from scripts.Tools import w
from scripts.logger import logger

print(paddleocr.__version__)
class OCRProcessor:
    def __init__(self,sensitivity = 0.5, lang='ch', use_gpu=False):
        """Initialize OCR with specified model paths."""
        self.ocr = PaddleOCR(
            use_angle_cls=False,  # Set to True if you have a direction classification model
            det_model_dir=PM.get_env("OCR_DET_PATH"),
            rec_model_dir=PM.get_env("OCR_REC_PATH"),
            lang=lang,
            use_gpu=use_gpu
        )
        self.sensitivity = sensitivity
    
    def process_image(self,image_path) -> str:
        """Run OCR on the given image and display the results."""
        results = self.ocr.ocr(image_path, cls=False)
        final_str = ""
        for line in results[0]:
            box, (text, score) = line
            if score > self.sensitivity:
                final_str += text + "\n"
        # 写入文件
        to_file = PM.get_path("EXTRACTED_DIR_PATH", file_name=f"OCR_result_{unique_name() + '.txt'}")
        w(to_file, final_str)
        return {"file_processed": to_file, "file_original": image_path}

