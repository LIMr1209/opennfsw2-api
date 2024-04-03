import base64
import gzip
import os
from typing import Any, Union

import uvicorn
from fastapi import FastAPI, APIRouter, Body, Request
from pydantic import BaseModel, Field
from fastapi.responses import Response
from starlette import status
from starlette.responses import JSONResponse, FileResponse
from inference_log import logger

inference_status = True

from inference_library import infer_service, load_model

load_model()

# 输入
input_dir = "input_data"
if not os.path.exists(input_dir):
    os.mkdir(input_dir)


def server_response(*, code=200, data: Union[list, dict, str] = None, message="Success") -> Response:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'code': code,
            'message': message,
            'data': data,
        }
    )


app = FastAPI()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常
    """
    logger.exception("全局异常捕获")
    return server_response(code=500, message=str(exc))


router = APIRouter()


class InterData(BaseModel):
    data_bs64: str = Field(description="视频或者图片bs64")
    suffix: str = Field(description="文件后缀")
    kind: int = Field(1, le=2, ge=1, description="1 视频 2 图片 3 图片压缩包")
    gzip: bool = Field(True, description="gzip是否压缩")


@router.post("/infer")
def infer(
        data: InterData
):
    global inference_status
    d = data.model_dump()
    try:
        u_data = base64.b64decode(data.data_bs64)
        if data.gzip:
            u_data = gzip.decompress(u_data)
        d.pop("data_bs64")
        d.pop("gzip")
        d["data"] = u_data
    except Exception as e:
        return server_response(code=400, message="Please provide the correct base64 code for the video!")
    inference_status = False
    code, res = infer_service(
        input_dir=input_dir, **d
    )
    inference_status = True
    if code == 200:
        return server_response(code=200, data=res)
    else:
        return server_response(code=code, message=res)


@router.get("/healthz")
def healthz():
    return server_response(code=200)


@router.get("/readyz")
def readyz():
    global inference_status
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'status': inference_status
        }
    )


app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app=app, host="0.0.0.0", port=13000)
