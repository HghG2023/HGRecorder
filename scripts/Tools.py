from .logger import logger
from .path_control import PM

def w(file, text):
    try:
        with open(file, 'w', encoding=PM.get_env("ENCODING")) as f:
            f.write(text)
    except Exception as e:
        logger.error(f"Error writing to {file}: {e}\n lose content {text}")

def r(file):
    try:
        with open(file, 'r', encoding=PM.get_env("ENCODING")) as f:
            res = f.read()
            return res
    except Exception as e:
        logger.error(f"Error read to {file}: {e}")

    return ""