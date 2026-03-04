"""调试模式日志配置"""
import logging
import sys


def setup_logger(debug_mode: bool = False) -> logging.Logger:
    """根据 Debug_Mode 配置日志级别"""
    logger = logging.getLogger("xiangxu")
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
