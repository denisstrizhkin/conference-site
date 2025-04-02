from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status, Request, Form
from fastapi.responses import HTMLResponse

from src.depends import Templates

router = APIRouter()


@router.get("/register")
def register(templates: Templates, request: Request):
    return templates.TemplateResponse(
        request=request, name="user/register.jinja", context={"title": "StudConfAU"}
    )


@router.post("/register")
def create_user(email: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"email": email}
