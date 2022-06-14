#   get_stats.py
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

from jira import JIRA
from dotenv import load_dotenv  # type: ignore
import os

from pprint import pprint
from datetime import datetime

from libdashboardjira import (
    get_all_worklogs_by_user,
    get_average_work_hours_by_user,
    get_week_work_hours_by_user,
    get_average_work_hours_by_user_rolling,
)

if __name__ == "__main__":
    load_dotenv()

    as_date = datetime(2022, 6, 8)

    jira = JIRA(
        os.environ["jira_site_url"],
        basic_auth=(os.environ["jira_api_email"], os.environ["jira_api_token"]),
    )

    wl = get_all_worklogs_by_user(jira)

    pprint(get_week_work_hours_by_user(wl))
    pprint(get_average_work_hours_by_user(wl, start_date=datetime(2022, 5, 12)))
    pprint(get_average_work_hours_by_user_rolling(wl, start_date=datetime(2022, 5, 12)))
