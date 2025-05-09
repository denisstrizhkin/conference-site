from typing import Optional
from pathlib import Path

from fastapi import FastAPI, status, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.settings import settings
from src.schemas import ErrorContext
from src.depends import get_templates

from src.routers.index import index_router
from src.routers.user.router import user_router
from src.routers.files.router import file_router
from src.routers.auth.router import auth_router
from src.routers.vote.router import vote_router

openapi_url: Optional[str] = None
if settings.show_docs:
    openapi_url = "/openapi.json"

app = FastAPI(openapi_url=openapi_url)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)
app.include_router(index_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(file_router)
app.include_router(vote_router)


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return get_templates().TemplateResponse(
        request=request,
        name="error.jinja",
        context=ErrorContext(
            message="По вашему запросу ничего не найдено.",
            code=status.HTTP_404_NOT_FOUND,
        ).model_dump(),
    )


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_exception_handler(request: Request, exc: HTTPException):
    return get_templates().TemplateResponse(
        request=request,
        name="error.jinja",
        context=ErrorContext(
            message="Недостаточно прав.",
            code=status.HTTP_403_FORBIDDEN,
        ).model_dump(),
    )


@app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_exception_handler(request: Request, exc: HTTPException):
    return get_templates().TemplateResponse(
        request=request,
        name="error.jinja",
        context=ErrorContext(
            message="Ошибка сервера.",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ).model_dump(),
    )


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(
        url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
    )
