import logging
from .path_control import PM 
from scripts.get_date_formate import today

def get_logger(name: str = "HGRecorder") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 Handler
    if logger.hasHandlers():
        return logger

    # 日志文件名为当前日期
    log_file = str(PM.get_env("LOG_DIR_PATH"))+f"/{today()}.log"

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding = PM.get_env("ENCODING"))
    file_handler.setLevel(logging.INFO)

    # 设置日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)

    return logger


logger = get_logger()