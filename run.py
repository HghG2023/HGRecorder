from pathlib import Path
import threading
import uvicorn
from app.API import create_api_app
from app.detect_folder import start_watch
from app.ASR import ASEProcessor
from app.OCR import OCRProcessor
from app.NER_1_re import NERProcessor
from scripts.path_control import PM
from scripts.logger import logger
from scripts.Tools import r
from scripts.DBprocessor import ProcessDB

# 初始化处理器实例
asr_processor = ASEProcessor()
ocr_processor = OCRProcessor()
ner_processor = NERProcessor()


def handle_new_file(file_path: str):
    """处理监控到的新文件，根据类型分发到ASR或OCR处理"""
    try:
        file_ext = file_path.lower().split('.')[-1]
        
        # 定义支持的音频和图像文件格式
        audio_extensions = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}
        image_extensions = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}
        text_extensions = {'txt'}
        
        # if file_ext in text_extensions:
        #     logger.info(f"检测到文本文件，跳过处理: {file_path}")
        #     return
        
        if file_ext in audio_extensions:
            logger.info(f"检测到音频文件，开始ASR处理: {file_path}")
            result = asr_processor.process_audio(file_path)
            logger.info(f"ASR处理完成，结果保存至: {result['file_processed']}")
            
        elif file_ext in image_extensions:
            logger.info(f"检测到图像文件，开始OCR处理: {file_path}")
            result = ocr_processor.process_image(file_path)
            logger.info(f"OCR处理完成，结果保存至: {result['file_processed']}")

        elif file_ext in text_extensions:
            logger.info(f"检测到文本文件，开始NER处理: {file_path}")
            result = {'file_processed':file_path, 'file_original':file_path }

        else:
            logger.warning(f"不支持的文件类型: {file_path}")
            raise

        # 文本处理, 合并dict
        res_dict = ner_processor.process_text(result['file_processed']) | result
        
        # 数据存储
        c_db = ProcessDB()
        c_db.create_event(res_dict)

    except Exception as e:
        logger.exception(f"文件处理失败 {file_path}: {str(e)}")
        raise 

def start_monitoring():
    """启动文件夹监控线程"""
    watch_dir = PM.get_env("UPLOAD_DIR_PATH")
    try:
        start_watch(
            folder_to_watch=watch_dir,
            user_callback=handle_new_file,
            stable_seconds=10.0  # 等待文件稳定的时间
        )
    except Exception as e:
        logger.exception(f"文件夹监控启动失败: {str(e)}")

def main():
    # 启动文件夹监控（后台线程）
    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitor_thread.start()
    logger.info("文件监控线程已启动")

    # 启动API服务
    app = create_api_app()
    logger.info("准备启动API服务...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # 允许所有网络接口访问
        port=8000,       # 端口号，可根据需要修改
        log_level="info"
    )



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except Exception as e:
        logger.exception(f"程序运行出错: {str(e)}")