#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BiliNote最终版打包脚本 - 修复所有已知问题
使用方法：python FINAL_BUILD_SCRIPT.py
"""

import os
import sys
import subprocess
from pathlib import Path

def find_ssl_dlls():
    """自动查找SSL DLL文件"""
    possible_paths = [
        "F:/tools/python_AI/Library/bin",
        "C:/Python312/DLLs", 
        "C:/Users/{}/anaconda3/Library/bin".format(os.environ.get("USERNAME", "")),
        "C:/ProgramData/anaconda3/Library/bin",
        "C:/Python39/DLLs",
    ]
    
    ssl_dll = None
    crypto_dll = None
    
    for path in possible_paths:
        if os.path.exists(path):
            ssl_files = [f for f in os.listdir(path) if f.startswith("libssl") and f.endswith(".dll")]
            crypto_files = [f for f in os.listdir(path) if f.startswith("libcrypto") and f.endswith(".dll")]
            
            if ssl_files:
                ssl_dll = os.path.join(path, ssl_files[0])
                print(f"✅ 找到SSL DLL: {ssl_dll}")
            if crypto_files:
                crypto_dll = os.path.join(path, crypto_files[0])
                print(f"✅ 找到Crypto DLL: {crypto_dll}")
    
    return ssl_dll, crypto_dll

def build_final_exe():
    """打包最终版BiliNote后端"""
    print("🚀 BiliNote最终版打包脚本")
    print("=" * 50)
    
    # 查找SSL DLL
    print("\n🔍 查找SSL DLL文件...")
    ssl_dll, crypto_dll = find_ssl_dlls()
    
    if not ssl_dll or not crypto_dll:
        print("❌ 未找到SSL DLL文件，请手动指定路径")
        return False
    
    # 构建PyInstaller命令 - 包含所有必要的依赖
    cmd = [
        "pyinstaller",
        "--name", "BiliNote-Backend-Final",
        "--onefile", 
        "--console",
        "--icon", "frontend_dist/dist/icon.ico",  # 关键：添加应用图标
        "--add-data", "app;app",
        "--add-data", "config;config",
        "--add-data", "static;static", 
        "--add-data", "fonts;fonts",
        "--add-data", "models;models",
        "--add-data", ".env.example;.",
        "--add-data", "events;events",  # 关键：添加events模块
        "--add-data", "ffmpeg_helper.py;.",  # 关键：添加ffmpeg_helper
        "--add-data", "frontend_dist;frontend_dist",  # 关键：添加前端文件
        "--add-binary", f"{ssl_dll};.",
        "--add-binary", f"{crypto_dll};.",
        "--add-binary", "E:\\AI\\AI_Plus\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe;.\\",
        "--add-binary", "E:\\AI\\AI_Plus\\ffmpeg-7.1.1-essentials_build\\bin\\ffplay.exe;.\\",
        "--add-binary", "E:\\AI\\AI_Plus\\ffmpeg-7.1.1-essentials_build\\bin\\ffprobe.exe;.\\",
        "--collect-all", "sqlalchemy",  # 关键：收集SQLAlchemy的所有子模块
        "--collect-all", "openai",
        "--collect-all", "faster_whisper",
        "--collect-all", "yt_dlp",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "pydantic", 
        "--hidden-import", "ffmpeg",
        "--hidden-import", "av",
        "--hidden-import", "PIL",
        "--hidden-import", "requests",
        "--hidden-import", "aiofiles",
        "--hidden-import", "multipart",
        "--hidden-import", "jinja2",
        "--hidden-import", "asyncio",
        "--hidden-import", "websockets", 
        "--hidden-import", "anyio",
        "--hidden-import", "starlette",
        "--hidden-import", "click",
        "--hidden-import", "python_dotenv",
        "--hidden-import", "gmssl",
        "--hidden-import", "modelscope",
        "--hidden-import", "tqdm",
        "--hidden-import", "blinker",
        "--hidden-import", "celery",
        "--hidden-import", "kombu",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib", 
        "--exclude-module", "numpy.testing",
        "--exclude-module", "pandas",
        "--exclude-module", "IPython",
        "main.py"
    ]
    
    print(f"\n📦 开始打包...预计需要5-10分钟")
    print("执行命令:", " ".join(cmd[:15]) + "...")
    
    try:
        # 清理之前的构建文件
        import shutil
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            for f in os.listdir("dist"):
                if f.startswith("BiliNote-Backend-Final"):
                    os.remove(os.path.join("dist", f))
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=".", timeout=600)
        print("✅ 打包成功!")
        
        # 检查输出文件
        exe_path = os.path.join("dist", "BiliNote-Backend-Final.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024*1024)
            print(f"✅ 可执行文件: {exe_path}")
            print(f"📦 文件大小: {size_mb:.2f} MB")
            print(f"🌐 启动后访问: http://127.0.0.1:8483")
            print("\n📋 使用说明：")
            print("1. 双击运行可执行文件")
            print("2. 等待服务启动（看到数据库初始化信息）")
            print("3. 在浏览器中访问: http://127.0.0.1:8483")
            return True
        else:
            print("❌ 警告: 未找到生成的可执行文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        print("错误输出:", e.stderr)
        return False

def main():
    # 执行打包
    success = build_final_exe()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()