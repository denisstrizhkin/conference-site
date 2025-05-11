from typing import Optional

from pydantic import BaseModel
from fastapi import UploadFile

from src.routers.user.schemas import UserContext

from .models import Reports


class VoteFormContext(UserContext):
    selected: Optional[Reports] = None
    reports: list[tuple[Reports, str]] = [
        (
            Reports.a,
            (
                "Шляга Елена - «Торцевой полупроводниковый лазер "
                "на основе оптических таммовских состояний»"
            ),
        ),
        (
            Reports.b,
            (
                "Плешаков Павел - «Использование микрофлюидики для "
                "формирования альгинатных микрогелей с клетками для "
                "использования в качестве моделей тканей и органов»"
            ),
        ),
        (
            Reports.c,
            (
                "Курилова Анастасия - «Синтез и дизайн гибких "
                "металлоорганических каркасов для оптического определения "
                "органических соединений»"
            ),
        ),
        (Reports.d, "Фофонов Михаил - «О топологической запутанности белков»"),
        (
            Reports.e,
            "Третьяков Иван - «О тропической математике и "
            "применении к алгоритмам»",
        ),
    ]


class VoteForm(BaseModel):
    code: str
    report: Reports


class VoteAdminContext(UserContext):
    image: str


class CodesForm(BaseModel):
    codes_file: str | UploadFile
