"""
异步工具函数

提供后台线程执行能力,用于不阻塞主流程的异步任务
"""

import threading
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def run_in_background(func: Callable, *args, **kwargs) -> None:
    """
    在后台线程中执行函数,不阻塞主流程
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数
    
    Example:
        >>> def sync_data(machine_id, mold_id):
        ...     # 同步逻辑
        ...     pass
        >>> 
        >>> run_in_background(sync_data, machine_id=1, mold_id=100)
    """
    def wrapper():
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Background task failed: {func.__name__}, error: {e}", exc_info=True)
    
    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
