import os
import subprocess
import sys
from pathlib import Path
from dotenv import dotenv_values, find_dotenv

from app.utils.logger import get_logger
logger = get_logger(__name__)


def _get_dotenv_path() -> str | None:
    if getattr(sys, "frozen", False):
        p = Path(sys.executable).resolve().parent / ".env"
        return str(p) if p.exists() else None
    p = find_dotenv()
    return p if p else None


def _normalize_ffmpeg_path(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    raw = value.strip().strip('"').strip("'")
    if not raw:
        return None, None

    if os.path.isfile(raw):
        return os.path.dirname(raw), raw
    if os.path.isdir(raw):
        return raw, os.path.join(raw, "ffmpeg.exe")

    return None, None


def _get_ffmpeg_candidates() -> list[tuple[str, str | None]]:
    candidates: list[tuple[str, str | None]] = []

    # 1. 优先从应用内部查找 FFmpeg（打包后的环境）
    if getattr(sys, '_MEIPASS', False):
        # 打包后的环境，从应用内部查找 FFmpeg
        internal_ffmpeg_path = str(Path(sys._MEIPASS) / "ffmpeg.exe")
        if os.path.exists(internal_ffmpeg_path):
            candidates.append(("internal", internal_ffmpeg_path))

    # 2. 从环境变量查找
    os_env_value = os.environ.get("FFMPEG_BIN_PATH")
    bin_dir, exe_path = _normalize_ffmpeg_path(os_env_value)
    if bin_dir:
        candidates.append(("env", exe_path))

    # 3. 从 .env 文件查找
    dotenv_path = _get_dotenv_path()
    if dotenv_path:
        dotenv_value = dotenv_values(dotenv_path).get("FFMPEG_BIN_PATH")
        bin_dir2, exe_path2 = _normalize_ffmpeg_path(dotenv_value)
        if bin_dir2:
            candidates.append(("dotenv", exe_path2))

    return candidates


def _prepend_path(dir_path: str | None) -> None:
    if not dir_path:
        return
    os.environ["PATH"] = dir_path + os.pathsep + os.environ.get("PATH", "")


def _resolve_ffmpeg_command() -> list[str]:
    candidates = _get_ffmpeg_candidates()
    logger.info(
        "FFMPEG_BIN_PATH env=%s dotenv=%s",
        os.environ.get("FFMPEG_BIN_PATH"),
        (dotenv_values(p).get("FFMPEG_BIN_PATH") if (p := _get_dotenv_path()) else None),
    )

    for source, exe_path in candidates:
        if exe_path and os.path.isfile(exe_path):
            _prepend_path(os.path.dirname(exe_path))
            logger.info("Using ffmpeg from %s: %s", source, exe_path)
            return [exe_path, "-version"]

    # Fallback to system PATH
    logger.info("Using ffmpeg from system PATH")
    return ["ffmpeg", "-version"]


def check_ffmpeg_exists() -> bool:
    """
    检查 ffmpeg 是否可用。优先使用 FFMPEG_BIN_PATH 环境变量指定的路径。
    """
    try:
        cmd = _resolve_ffmpeg_command()
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("ffmpeg 已安装")
        return True
    except (FileNotFoundError, OSError, subprocess.CalledProcessError):
        logger.info("ffmpeg 未安装")
        return False


def ensure_ffmpeg_or_raise():
    """
    校验 ffmpeg 是否可用，否则抛出异常并提示安装方式。
    """
    if not check_ffmpeg_exists():
        logger.error("未检测到 ffmpeg，请先安装后再使用本功能。")
        raise EnvironmentError(
            " 未检测到 ffmpeg，请先安装后再使用本功能。\n"
            "👉 下载地址：https://ffmpeg.org/download.html\n"
            "🪟 Windows 推荐：https://www.gyan.dev/ffmpeg/builds/\n"
            "💡 如果你已安装，请将其路径写入 `.env` 文件，例如：\n"
            "FFMPEG_BIN_PATH=/your/custom/ffmpeg/bin"
        )