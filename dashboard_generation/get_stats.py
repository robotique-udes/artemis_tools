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
    get_all_worklogs_by_issue,
    get_average_work_hours_by_user,
    get_week_work_hours_by_user,
    get_average_work_hours_by_user_rolling,
    get_all_issues,
    issues_by_key,
    WorklogIssue,
    get_all_epics_by_key,
    sum_time_estimate_by_epic,
)

if __name__ == "__main__":
    load_dotenv()

    as_date = datetime.today()
    hour = 0

    jira = JIRA(
        os.environ["jira_site_url"],
        basic_auth=(os.environ["jira_api_email"], os.environ["jira_api_token"]),
    )

    iss = get_all_issues(jira)
    diss = issues_by_key(iss)
    dwliss = get_all_worklogs_by_issue(jira, diss)
    wl = get_all_worklogs_by_user(dwliss)
    dep = get_all_epics_by_key(jira)

    all_wl: list[WorklogIssue] = []
    for user in wl:
        all_wl.extend(wl[user])

    print("Semaine")
    pprint(get_week_work_hours_by_user(wl, hour=hour), indent=2)
    print("Moyenne")
    pprint(
        get_average_work_hours_by_user(wl, start_date=datetime(2022, 5, 12, 12)),
        indent=2,
    )
    print("Moyenne roulante")
    pprint(
        get_average_work_hours_by_user_rolling(
            wl, start_date=datetime(2022, 5, 12, 12)
        ),
        indent=2,
    )

    # print("Epic")
    # pprint(
    #     {
    #         dep[k].fields.summary: v
    #         for k, v in sum_time_estimate_by_epic(
    #             issues_dict=diss, epics_dict=dep
    #         ).items()
    #     }
    # )

    # pprint(diss["AR-5"].raw)
