import urllib

from fastapi import APIRouter, Request, Response

from src.routers.auth.depends import CurrentUser, allowed_id_or_roles
from src.routers.user.models import UserRole

from src.controllers.user_controller import UserControllerDep

file_router = APIRouter(prefix="/files")


@file_router.get("/{file_id}")
async def download_file(
    file_id: int,
    request: Request,
    current_user: CurrentUser,
    user_controller: UserControllerDep,
):
    allowed_id_or_roles(current_user, current_user.id, [UserRole.admin])
    file = await user_controller.get_file(current_user, file_id)
    file_name = urllib.parse.quote(file.name.encode("utf8"))
    return Response(
        content=file.content,
        media_type=file.type,
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{file_name}",
            "Content-Length": str(len(file.content)),
        },
    )
