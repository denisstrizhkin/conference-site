from pathlib import Path

from fastapi import FastAPI, status, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from src.schemas import BaseContext
from src.depends import get_templates
from src.routers import IndexRouter
from src.routers.user import UserRouter
from src.routers.files import FileRouter


app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)
app.include_router(IndexRouter)
app.include_router(UserRouter)
app.include_router(FileRouter)


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return get_templates().TemplateResponse(
        request=request, name="404.jinja", context=BaseContext().model_dump()
    )
