from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.routers import IndexRouter
from src.routers.user import UserRouter

app = FastAPI()
app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)
app.include_router(IndexRouter)
app.include_router(UserRouter, prefix="/user")

templates = Jinja2Templates(directory="templates")
