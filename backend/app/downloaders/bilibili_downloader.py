import os
from abc import ABC
from typing import Union, Optional

import yt_dlp

from app.downloaders.base import Downloader, DownloadQuality, QUALITY_MAP
from app.models.notes_model import AudioDownloadResult
from app.utils.path_helper import get_data_dir
from app.utils.url_parser import extract_video_id


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or not v.strip():
        return default
    try:
        return int(v)
    except ValueError:
        return default


class BilibiliDownloader(Downloader, ABC):
    def __init__(self):
        super().__init__()

    def download(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
        quality: DownloadQuality = "fast",
        need_video: Optional[bool] = False
    ) -> AudioDownloadResult:
        if output_dir is None:
            output_dir = get_data_dir()
        if not output_dir:
            output_dir = self.cache_data
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")

        proxy = os.getenv("YTDLP_PROXY")
        socket_timeout = os.getenv("YTDLP_SOCKET_TIMEOUT")
        retries = _env_int("YTDLP_RETRIES", 3)
        no_check_cert = _env_bool("YTDLP_NO_CHECK_CERTIFICATE", False)
        force_ipv4 = _env_bool("YTDLP_FORCE_IPV4", False)
        user_agent = os.getenv(
            "YTDLP_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        )

        ffmpeg_bin_path = os.getenv("FFMPEG_BIN_PATH")
        ffmpeg_location = None
        if ffmpeg_bin_path:
            candidate = os.path.join(ffmpeg_bin_path, "ffmpeg.exe")
            ffmpeg_location = candidate if os.path.isfile(candidate) else ffmpeg_bin_path

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',
                }
            ],
            'noplaylist': True,
            'quiet': False,
        }

        if proxy is not None:
            ydl_opts["proxy"] = proxy
        if socket_timeout and socket_timeout.strip():
            try:
                ydl_opts["socket_timeout"] = float(socket_timeout)
            except ValueError:
                pass

        ydl_opts["retries"] = retries
        ydl_opts["fragment_retries"] = retries
        ydl_opts["nocheckcertificate"] = no_check_cert
        ydl_opts["http_headers"] = {"User-Agent": user_agent, "Referer": "https://www.bilibili.com/"}
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = ffmpeg_location
        if force_ipv4:
            ydl_opts["source_address"] = "0.0.0.0"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get("id")
            title = info.get("title")
            duration = info.get("duration", 0)
            cover_url = info.get("thumbnail")
            audio_path = os.path.join(output_dir, f"{video_id}.mp3")

        return AudioDownloadResult(
            file_path=audio_path,
            title=title,
            duration=duration,
            cover_url=cover_url,
            platform="bilibili",
            video_id=video_id,
            raw_info=info,
            video_path=None  # ❗音频下载不包含视频路径
        )

    def download_video(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
    ) -> str:
        """
        下载视频，返回视频文件路径
        """

        if output_dir is None:
            output_dir = get_data_dir()
        os.makedirs(output_dir, exist_ok=True)
        print("video_url",video_url)
        video_id=extract_video_id(video_url, "bilibili")
        video_path = os.path.join(output_dir, f"{video_id}.mp4")
        if os.path.exists(video_path):
            return video_path

        # 检查是否已经存在


        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")

        proxy = os.getenv("YTDLP_PROXY")
        socket_timeout = os.getenv("YTDLP_SOCKET_TIMEOUT")
        retries = _env_int("YTDLP_RETRIES", 3)
        no_check_cert = _env_bool("YTDLP_NO_CHECK_CERTIFICATE", False)
        force_ipv4 = _env_bool("YTDLP_FORCE_IPV4", False)
        user_agent = os.getenv(
            "YTDLP_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        )

        ffmpeg_bin_path = os.getenv("FFMPEG_BIN_PATH")
        ffmpeg_location = None
        if ffmpeg_bin_path:
            candidate = os.path.join(ffmpeg_bin_path, "ffmpeg.exe")
            ffmpeg_location = candidate if os.path.isfile(candidate) else ffmpeg_bin_path

        ydl_opts = {
            'format': 'bv*[ext=mp4]/bestvideo+bestaudio/best',
            'outtmpl': output_path,
            'noplaylist': True,
            'quiet': False,
            'merge_output_format': 'mp4',  # 确保合并成 mp4
        }

        if proxy is not None:
            ydl_opts["proxy"] = proxy
        if socket_timeout and socket_timeout.strip():
            try:
                ydl_opts["socket_timeout"] = float(socket_timeout)
            except ValueError:
                pass

        ydl_opts["retries"] = retries
        ydl_opts["fragment_retries"] = retries
        ydl_opts["nocheckcertificate"] = no_check_cert
        ydl_opts["http_headers"] = {"User-Agent": user_agent, "Referer": "https://www.bilibili.com/"}
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = ffmpeg_location
        if force_ipv4:
            ydl_opts["source_address"] = "0.0.0.0"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get("id")
            video_path = os.path.join(output_dir, f"{video_id}.mp4")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件未找到: {video_path}")

        return video_path

    def delete_video(self, video_path: str) -> str:
        """
        删除视频文件
        """
        if os.path.exists(video_path):
            os.remove(video_path)
            return f"视频文件已删除: {video_path}"
        else:
            return f"视频文件未找到: {video_path}"