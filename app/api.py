import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.db.db import DB
from app.exceptions import CommonException, InternalServerError
from app.routers.items import basic_router, additional_router

app = FastAPI(title='Mega Market Open API', description='Вступительное задание в Летнюю Школу Бэкенд Разработки Яндекса 2022')
logger = logging.getLogger(__name__)

@app.on_event('startup')
async def startup() -> None:
    await DB.connect_db()

@app.on_event('shutdown')
async def shutdown() -> None:
    await DB.disconnect_db()

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
        content={
            'code': exception.code,
            'message': exception.error
        }
    )
app.include_router(basic_router)
app.include_router(additional_router)