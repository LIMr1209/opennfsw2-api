import asyncio
import base64
import ctypes
import gzip
import os
import threading
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Union, Callable, Awaitable

import uvicorn
from asyncer import asyncify
from anyio.lowlevel import RunVar
from anyio import CapacityLimiter
from fastapi import FastAPI, APIRouter, Body, Request, HTTPException
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("start")
    RunVar("_default_thread_limiter").set(CapacityLimiter(5000))
    yield


app = FastAPI(lifespan=lifespan)


# lock = threading.Lock()


async def disconnect_poller(request: Request, result: Any):
    """
    Poll for a disconnect.
    If the request disconnects, stop polling and return.
    """
    try:
        while not await request.is_disconnected():
            await asyncio.sleep(0.01)

        print("Request disconnected")

        return result
    except asyncio.CancelledError:
        pass
        # print("Stopping polling loop")


def cancel_on_disconnect(handler: Callable[[Request], Awaitable[Any]]):
    """
    Decorator that will check if the client disconnects,
    and cancel the task if required.
    """

    @wraps(handler)
    async def cancel_on_disconnect_decorator(request: Request, *args, **kwargs):
        sentinel = object()

        # Create two tasks, one to poll the request and check if the
        # client disconnected, and another which is the request handler
        poller_task = asyncio.ensure_future(disconnect_poller(request, sentinel))
        handler_task = asyncio.ensure_future(handler(request, *args, **kwargs))

        done, pending = await asyncio.wait(
            [poller_task, handler_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel any outstanding tasks
        for t in pending:
            t.cancel()

            try:
                await t
            except asyncio.CancelledError:
                print(f"{t} was cancelled")
            except Exception as exc:
                print(f"{t} raised {exc} when being cancelled")

        # Return the result if the handler finished first
        if handler_task in done:
            return await handler_task
        if hasattr(request, "thread_id"):
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(request.thread_id),
                                                       ctypes.py_object(SystemExit))
        # Otherwise, raise an exception
        # This is not exactly needed, but it will prevent
        # validation errors if your request handler is supposed
        # to return something.
        print("Raising an HTTP error because I was disconnected!!")
        # lock.acquire()
        global inference_status
        inference_status = True
        # lock.release()
        raise HTTPException(503)

    return cancel_on_disconnect_decorator


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
@cancel_on_disconnect
async def infer(
        request: Request,
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
    # lock.acquire()
    inference_status = False
    # lock.release()
    code, res = await asyncify(infer_service, cancellable=True)(request=request, input_dir=input_dir, **d)
    # lock.acquire()
    inference_status = True
    # lock.release()
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
