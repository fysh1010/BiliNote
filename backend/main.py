import os
import threading
import time
import webbrowser
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.db.init_db import init_db
from app.db.provider_dao import seed_default_providers
from app.exceptions.exception_handlers import register_exception_handlers
# from app.db.model_dao import init_model_table
# from app.db.provider_dao import init_provider_table
from app.utils.logger import get_logger
from app import create_app
from app.transcriber.transcriber_provider import get_transcriber
# from events import register_handler  # 该模块不存在，暂时注释
from ffmpeg_helper import ensure_ffmpeg_or_raise

logger = get_logger(__name__)

if getattr(sys, "frozen", False):
    RUNTIME_DIR = Path(sys.executable).resolve().parent
    load_dotenv(RUNTIME_DIR / ".env")
else:
    RUNTIME_DIR = Path(__file__).resolve().parent
    load_dotenv()

print("BiliNote 正在启动... 首次启动可能需要几十秒，请耐心等待（不要关闭窗口）", flush=True)

# 读取 .env 中的路径
static_path = os.getenv('STATIC', '/static')
out_dir = os.getenv('OUT_DIR')

# 自动创建本地目录（static 和 static/screenshots）
static_dir = str(RUNTIME_DIR / "static")
uploads_dir = str(RUNTIME_DIR / "uploads")
if out_dir is None:
    out_dir = str(Path(static_dir) / "screenshots")

if not os.path.exists(static_dir):
    os.makedirs(static_dir)
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # register_handler()  # 该函数不存在，暂时注释
    print("[1/3] 正在初始化数据库...", flush=True)
    init_db()

    print("[2/3] 正在初始化转录器...", flush=True)
    get_transcriber(transcriber_type=os.getenv("TRANSCRIBER_TYPE", "fast-whisper"))

    print("[3/3] 正在加载默认 Provider...", flush=True)
    seed_default_providers()
    yield

app = create_app(lifespan=lifespan)

serve_frontend = os.getenv("SERVE_FRONTEND", "false").lower() in {"1", "true", "yes", "y", "on"}

if serve_frontend:
    # 前端静态文件配置（默认关闭；仅在 SERVE_FRONTEND=true 时启用）
    # 支持 PyInstaller 打包环境
    if hasattr(sys, '_MEIPASS'):
        # 打包后的环境
        FRONTEND_DIR = Path(sys._MEIPASS) / "frontend_dist" / "dist"
    else:
        # 开发环境
        FRONTEND_DIR = Path(__file__).parent / "frontend_dist" / "dist"

    # 只有在前端构建目录存在时才挂载静态文件
    if FRONTEND_DIR.exists() and (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

        @app.get("/")
        def index():
            html_content = (FRONTEND_DIR / "index.html").read_text(encoding='utf-8')
            html_content = html_content.replace('href="./', 'href="/')
            html_content = html_content.replace('src="./', 'src="/')
            return HTMLResponse(content=html_content)

        @app.get("/icon.svg")
        def icon():
            return FileResponse(
                FRONTEND_DIR / "icon.svg",
                media_type="image/svg+xml",
                headers={"Cache-Control": "public, max-age=3600"}
            )

        @app.get("/favicon.ico")
        def favicon():
            if (FRONTEND_DIR / "icon.svg").exists():
                return RedirectResponse(url="/icon.svg", status_code=307)
            return FileResponse(FRONTEND_DIR / "icon.ico")

        @app.get("/placeholder.png")
        def placeholder():
            return FileResponse(FRONTEND_DIR / "placeholder.png")

        @app.get("/.src/assets/placeholder.png")
        def placeholder_src():
            return FileResponse(FRONTEND_DIR / "placeholder.png")
    else:
        @app.get("/")
        def index():
            return {"message": "BiliNote Backend API is running. Frontend build directory not found."}
else:
    @app.get("/")
    def index():
        return {"message": "BiliNote Backend API is running."}

origins = [
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  #  加上 Tauri 的 origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.mount(static_path, StaticFiles(directory=static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


def open_browser():
    """自动打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    port = int(os.getenv("BACKEND_PORT", 8483))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    access_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    webbrowser.open(f"http://{access_host}:{port}")


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8483))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    access_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    access_url = f"http://{access_host}:{port}"
    print("服务启动中，请稍候...", flush=True)
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Open this URL in your browser: {access_url}")
    
    # 启动线程自动打开浏览器（已禁用）
    # auto_open = os.getenv("AUTO_OPEN_BROWSER", "true").lower() in {"1", "true", "yes", "y", "on"}
    # if auto_open:
    #     threading.Thread(target=open_browser).start()
    
    uvicorn.run(app, host=host, port=port, reload=False)