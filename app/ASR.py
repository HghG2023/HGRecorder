import whisper
from dotenv import load_dotenv
from opencc import OpenCC
import os

from scripts.Tools import w
from scripts.path_control import PM
from scripts.unique_string_generate import unique_name

load_dotenv()
ASR_MODEL_PATH = os.getenv("ASR_MODEL_PATH")


class ASEProcessor:
    def __init__(self):
        self.model = whisper.load_model(ASR_MODEL_PATH)

    def convert_t2s(self, text):

        try:
            cc = OpenCC('t2s')
            return cc.convert(text)
        except Exception:
            return text

    def process_audio(self, target_path):
        res_txt = self.model.transcribe(target_path)
        res = self.convert_t2s(res_txt["text"])
        # 写入文件
        to_file = PM.get_path("EXTRACTED_DIR_PATH", file_name=f"ASR_result_{unique_name() + '.txt'}")
        w(to_file, res)
        return {"file_processed": to_file, "file_original": target_path}

