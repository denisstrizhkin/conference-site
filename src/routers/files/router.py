import urllib

from fastapi import APIRouter, Request, Response, HTTPException, status

from src.db import Session
from src.routers.user.models import UserRole
from src.routers.auth.depends import CurrentUser

from .repo import FileRepository

file_router = APIRouter(prefix="/files")


@file_router.get("/{file_id}")
async def download_file(
    file_id: int,
    request: Request,
    current_user: CurrentUser,
    session: Session,
):
    if current_user.role != UserRole.admin:
        if current_user.form is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if current_user.form.file_id != file_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    file = await FileRepository(session).get_one_or_none(file_id)
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
