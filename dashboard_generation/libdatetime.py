#   libdatetime.py
#   Copyright (C) 2022  Philippe Warren
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

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


def get_next_day(
    day: int | Weekday, date: datetime = datetime.today(), hour: int = 11
) -> datetime:
    old_date = date.astimezone()
    date = date.astimezone().replace(hour=hour, minute=0, second=0, microsecond=0)

    days = ((day.value if isinstance(day, Weekday) else day) - (date.weekday() + 7)) % 7

    if days == 0 and old_date > date:
        days = 7

    return date + timedelta(days=days)


def get_last_day(
    day: int | Weekday, date: datetime = datetime.today(), hour: int = 11
) -> datetime:
    old_date = date.astimezone()
    date = date.astimezone().replace(hour=hour, minute=0, second=0, microsecond=0)

    days = (date.weekday() - (day.value if isinstance(day, Weekday) else day)) % 7

    if days == 0 and old_date < date:
        days = 7

    return date - timedelta(days=days)


def format_date(date: datetime) -> str:
    return strip_leading_zero(date.strftime("%d %B %Y"))


def format_date_file_postfix(date: datetime) -> str:
    return f"{date.strftime('%Y_%m_%d')}"


def s_to_h(seconds: int) -> float:
    return seconds / 3600
