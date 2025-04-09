import logging

from fastapi import APIRouter, Request, Response, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from src.depends import Templates
from src.db import Session
from src.routers.user.models import UserRole
from src.routers.user.auth import CurrentUser

from .repo import FileRepository

logger = logging.getLogger(__file__)

router = APIRouter(prefix="/files")


@router.get("/{file_id}")
async def download_file(
    file_id: int,
    request: Request,
    templates: Templates,
    current_user: CurrentUser,
    session: Session,
):
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="user/login.jinja",
            context={"title": "StudConfAU"},
        )

    if (
        current_user.form.file_id != file_id
        and current_user.role != UserRole.admin
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Попытка скачать чужой файл",
        )

    try:
        async with session() as session:
            file = await FileRepository(session).get(file_id)
    except SQLAlchemyError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e._message,
        )

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такого файла не существует",
        )

    return Response(
        content=file.content,
        media_type=file.type,
        headers={
            "Content-Disposition": f"attachment; filename={file.name}",
            "Content-Length": str(len(file.content)),
        },
    )
