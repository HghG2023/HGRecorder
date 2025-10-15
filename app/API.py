# API.py
import socket
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .API_work import create_app  # 引用app工厂


def _get_all_ipv4() -> list[str]:
    """获取所有可用的IPv4地址，用于显示服务访问地址"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return [s.getsockname()[0]]
    except OSError:
        return ["127.0.0.1"]


@asynccontextmanager
async def _api_lifespan(app: FastAPI):
    """API服务生命周期管理，仅处理API启动/关闭相关逻辑"""
    # 启动阶段：打印服务信息
    ips = _get_all_ipv4()
    logger = logging.getLogger("uvicorn.error")
    logger.info("✅ API服务已启动")
    for ip in ips:
        logger.info(f"🔗 服务访问地址：http://{ip}:8000")
    
    yield  # 服务运行中

    # 关闭阶段：打印关闭信息
    logger.info("🛑 API服务即将关闭")


def create_api_app() -> FastAPI:
    """创建并配置API应用实例，专注于API启动功能"""
    app = create_app()
    app.router.lifespan_context = _api_lifespan
    return app