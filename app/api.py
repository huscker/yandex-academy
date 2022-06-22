import logging
from time import perf_counter, ctime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.db.db import DB
from app.exceptions import CommonException, InternalServerError
from app.routers.users import users_router

origins = ["*"] # TODO: change it in bright future
app = FastAPI(title='Hackaton backend')
logger = logging.getLogger(__name__)

@app.on_event('startup')
async def startup() -> None:
    await DB.connect_db()

@app.on_event('shutdown')
async def shutdown() -> None:
    await DB.disconnect_db()

@app.middleware('http')
async def log_request(request: Request, pending_call):
    start_time = perf_counter()
    response = await pending_call(request)
    processed_time = (perf_counter() - start_time)
    formatted_time = '{0:.5f}'.format(processed_time)
    logger.info(f'{ctime()}: path={request.url.path}, method={request.method}, processed={formatted_time}')
    return response

@app.exception_handler(CommonException)
async def common_exception_handler(request: Request, exception: CommonException) -> JSONResponse:
    logger.error(exception.error)
    if isinstance(exception, InternalServerError):
        return JSONResponse(
            status_code=exception.code,
            content={'details': 'Internal Server Error'}
        )
    return JSONResponse(
        status_code=exception.code,
        content={'detatils': exception.error}
    )
app.include_router(users_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.mount('/static', StaticFiles(directory='static'), name='static')