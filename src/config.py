"""配置加载：.env、Debug_Mode、config.json 持久化"""
import json
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

from src.utils.logger import setup_logger

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 无 .env 时从 .env.example 复制一份
_env_file = PROJECT_ROOT / ".env"
_env_example = PROJECT_ROOT / ".env.example"
if not _env_file.exists() and _env_example.exists():
    shutil.copy(_env_example, _env_file)

# 加载 .env
load_dotenv()
CONFIG_PATH = PROJECT_ROOT / "config.json"
# 无 config.json 时从 config.json.example 复制一份（与 .env.example 一致）
_config_example = PROJECT_ROOT / "config.json.example"
if not CONFIG_PATH.exists() and _config_example.exists():
    shutil.copy(_config_example, CONFIG_PATH)

# Debug 模式
DEBUG_MODE = os.getenv("Debug_Mode", "False").lower() in ("true", "1", "yes")

# 全局 logger
logger = setup_logger(DEBUG_MODE)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


# 控制台主窗口：从 .env 读取。启动宽高（默认 920+1/5≈1104）、最小宽高
CONSOLE_WIDTH = _env_int("CONSOLE_WIDTH", 1104)
CONSOLE_HEIGHT = _env_int("CONSOLE_HEIGHT", 620)
CONSOLE_MIN_WIDTH = _env_int("CONSOLE_MIN_WIDTH", 920)
CONSOLE_MIN_HEIGHT = _env_int("CONSOLE_MIN_HEIGHT", 620)

# 小窗显示默认配置（可被“恢复默认”使用）
OVERLAY_DEFAULTS = {
    "overlay": {
        "width_pct": 30.0,
        "height_pct": 17.0,
        "corner_style": "rounded",  # rounded | square 圆角 / 直角
        "corner_radius": 20,  # 圆角弧度（像素），仅当 corner_style=rounded 时生效
        "simple_mode": True,  # 简洁模式：不显示「识别:」「翻译:」前缀
        "split_subtitle_mode": True,  # 拆分字幕：识别靠左、翻译靠右，单类型时奇偶行左右交替
        "bg_color": "#1a1a1a",
        "bg_alpha": 0.88,
        "font_family": "Microsoft YaHei",
        "font_size": 16,
        "text_color": "#e5e5e5",
        "text_alpha": 1.0,
        "line_spacing": 8,
        "align": "left",  # left | center | right
    }
}


def load_settings() -> dict:
    """从 config.json 加载用户设置"""
    default = {
        "api_key": "",
        "translation_target_languages": ["zh"],
        "console_width": CONSOLE_WIDTH,
        "console_height": CONSOLE_HEIGHT,
        **OVERLAY_DEFAULTS,
    }
    if not CONFIG_PATH.exists():
        return default
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 深度合并 overlay，保证缺失键用默认值
            merged = {**default, **data}
            if "overlay" in data:
                merged["overlay"] = {**OVERLAY_DEFAULTS["overlay"], **data["overlay"]}
            return merged
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("加载 config.json 失败: %s，使用默认配置", e)
        return default


def save_settings(settings: dict) -> None:
    """将用户设置持久化到 config.json"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        if DEBUG_MODE:
            logger.debug("设置已保存到 %s", CONFIG_PATH)
    except IOError as e:
        logger.error("保存 config.json 失败: %s", e)
        raise
