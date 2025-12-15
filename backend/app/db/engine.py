import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv, find_dotenv

if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    load_dotenv(exe_dir / ".env")
else:
    load_dotenv(find_dotenv())

def _default_sqlite_url() -> str:
    if getattr(sys, "frozen", False):
        db_path = Path(sys.executable).resolve().parent / "bili_note.db"
        return f"sqlite:///{db_path.as_posix()}"

    backend_dir = Path(__file__).resolve().parents[2]
    project_root = backend_dir.parent

    candidates = [
        project_root / "bili_note.db",
        backend_dir / "bili_note.db",
    ]

    for p in candidates:
        if p.exists():
            return f"sqlite:///{p.as_posix()}"

    p = backend_dir / "bili_note.db"
    return f"sqlite:///{p.as_posix()}"


# 默认 SQLite，如果想换 PostgreSQL 或 MySQL，可以直接改 .env
DATABASE_URL = os.getenv("DATABASE_URL") or _default_sqlite_url()

# SQLite 需要特定连接参数，其他数据库不需要
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    **engine_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_engine():
    return engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()