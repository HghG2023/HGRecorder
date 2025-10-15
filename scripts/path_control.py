from dotenv import load_dotenv
import os

class PathManager:
    def __init__(self):
        pass

    def get_env(self, env_var: str, default: str = "") -> str:
        env_value = os.getenv(env_var, default)
        if "DIR" in env_var and env_value:
            # 确保 env_value 不是 None 或空字符串
            os.makedirs(env_value, exist_ok=True)
        return env_value

    def get_path(self, enc_var: str, file_name: str) -> str:
        return os.path.join(self.get_env(enc_var), file_name)

load_dotenv()
PM = PathManager()