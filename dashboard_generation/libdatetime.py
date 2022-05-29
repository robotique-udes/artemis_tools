from datetime import datetime, timedelta
import re

from enum import Enum


class Weekday(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


# Set time locale to ctype locale
import locale

locale.setlocale(locale.LC_TIME, locale.getlocale())


def local_today() -> datetime:
    return datetime.today().astimezone()


def get_date(date: str) -> datetime:
    return datetime.fromisoformat(
        re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", date.replace("Z", "+00:00"))
    ).astimezone()


def date_is_in_last_seven_days(date: str) -> bool:
    return (local_today() - get_date(date)).days <= 7


def strip_leading_zero(date: str) -> str:
    return re.sub(r"^0", "", date)


def get_next_day(day: int | Weekday, date: datetime = datetime.today()) -> datetime:
    old_date = date.astimezone()
    date = date.astimezone().replace(hour=11, minute=0, second=0, microsecond=0)

    days = ((day.value if isinstance(day, Weekday) else day) - (date.weekday() + 7)) % 7

    if days == 0 and old_date > date:
        days = 7

    return date + timedelta(days=days)


def get_last_day(day: int | Weekday, date: datetime = datetime.today()) -> datetime:
    old_date = date.astimezone()
    date = date.astimezone().replace(hour=11, minute=0, second=0, microsecond=0)

    days = (date.weekday() - (day.value if isinstance(day, Weekday) else day)) % 7

    if days == 0 and old_date < date:
        days = 7

    return date - timedelta(days=days)
