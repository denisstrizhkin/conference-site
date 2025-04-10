import logging
import urllib

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
    if (
        current_user.form.file_id != file_id
        and current_user.role != UserRole.admin
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
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
        )

    file_name = urllib.parse.quote(file.name.encode("utf8"))
    return Response(
        content=file.content,
        media_type=file.type,
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{file_name}",
            "Content-Length": str(len(file.content)),
        },
    )
