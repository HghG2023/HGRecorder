import time
import threading
from pathlib import Path
from typing import Callable, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scripts.logger import logger

# -------------------------------------------------
# 1️⃣ 等待文件稳定
# -------------------------------------------------
def wait_until_file_stable(
    file_path: Union[str, Path],
    *,
    stable_seconds: float = 5.0,
    check_interval: float = 2.0,
    timeout: float = 300.0,
) -> Path:
    """
    等待文件稳定

    等待文件的大小和最后修改时间在一段时间内没有变化

    :param file_path: 文件路径
    :param stable_seconds: 文件稳定需要的时间（秒）
    :param check_interval: 检查间隔（秒）
    :param timeout: 超时时间（秒）
    :return: 文件的 Path 对象
    :raises FileNotFoundError: 文件不存在
    :raises TimeoutError: 等待超时
    """

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    last_size = file_path.stat().st_size
    last_mtime = file_path.stat().st_mtime
    unchanged_since = time.monotonic()
    deadline = time.monotonic() + timeout

    while True:
        time.sleep(check_interval)
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        stat = file_path.stat()
        if stat.st_size == last_size and stat.st_mtime == last_mtime:
            if time.monotonic() - unchanged_since >= stable_seconds:
                return file_path
        else:
            last_size, last_mtime = stat.st_size, stat.st_mtime
            unchanged_since = time.monotonic()

        if time.monotonic() > deadline:
            raise TimeoutError(f"等待文件稳定超时：{file_path}")


# -------------------------------------------------
# 2️⃣ 监控事件处理器
# -------------------------------------------------
class FolderHandler(FileSystemEventHandler):
    def __init__(self, user_callback: Callable[[str], None],
                 stable_seconds: float = 5.0):
        """
        Args:
            user_callback: 文件稳定后真正要执行的业务函数。
            stable_seconds: 文件大小/mtime 连续不变的时间阈值。
        """
        self.user_callback = user_callback
        self.stable_seconds = stable_seconds
        self.processing_files = set()  # 当前正在处理的文件路径
        self.lock = threading.Lock()   # 保证线程安全

    def on_created(self, event):
        if not event.is_directory:
            self._process_when_stable(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._process_when_stable(event.src_path)

    def on_deleted(self, event):
        pass

    def on_moved(self, event):
        pass

    def _process_when_stable(self, path: str):
        with self.lock:
            if path in self.processing_files:
                logger.debug(f"[跳过] 文件已在处理中：{path}")
                return
            self.processing_files.add(path)
            logger.debug(f"[加入处理队列] {path}")

        threading.Thread(
            target=self._wait_and_callback,
            args=(path,),
            daemon=True
        ).start()

    def _wait_and_callback(self, path: str):
        try:
            logger.info(f"[开始等待稳定] {path}")
            stable_path = wait_until_file_stable(
                path, stable_seconds=self.stable_seconds)
            logger.info(f"[文件稳定] {stable_path}")
            self.user_callback(str(stable_path))
        except (FileNotFoundError, TimeoutError) as exc:
            logger.warning(f"[跳过文件] {exc}")
        except Exception as e:
            logger.exception(f"[处理出错] {path}: {e}")
        finally:
            with self.lock:
                self.processing_files.discard(path)
                logger.debug(f"[移除处理队列] {path}")


# -------------------------------------------------
# 3️⃣ 启动监控器
# -------------------------------------------------
def start_watch(folder_to_watch: Path,
                user_callback: Callable[[str], None],
                stable_seconds: float = 10.0):
    """
    Args:
        folder_to_watch: 监听的文件夹路径。
        user_callback: 业务处理函数，参数为稳定后的文件路径。
        stable_seconds: 连续不变多少秒视为稳定。
    """
    if not isinstance(folder_to_watch,Path):
        folder_to_watch = Path(folder_to_watch)
        
    if not folder_to_watch.exists():
        raise FileNotFoundError(folder_to_watch)
    
    event_handler = FolderHandler(user_callback, stable_seconds)
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=True)
    observer.start()
    logger.info(f"📂 正在监控：{str(folder_to_watch)}（Ctrl+C 退出）")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    logger.info("🛑 文件监控已停止。")
