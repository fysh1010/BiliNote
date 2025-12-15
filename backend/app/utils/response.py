from fastapi.responses import JSONResponse
from app.utils.status_code import StatusCode
from pydantic import BaseModel
from typing import Optional, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ResponseWrapper:
    @staticmethod
    def success(data=None, msg="success", code=0):
        return JSONResponse(content={
            "code": code,
            "msg": msg,
            "data": data
        })

    @staticmethod
    def error(msg="error", code=500, data=None):
        logger.error(f"响应错误: code={code}, msg={msg}")
        return JSONResponse(content={
            "code": code,
            "msg": str(msg),
            "data": data
        })