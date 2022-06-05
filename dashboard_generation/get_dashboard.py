#   get_dashboard.py
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

from libdashboard import (
    get_sprint_name,
    get_sprint,
    get_sprint_dates_str,
    get_sprint_goal,
    # get_user,
    get_all_worklogs_by_user,
    # get_all_worklogs_by_user_for_week,
    # sum_worklogs,
    # filter_worklog_for_week,
    # get_all_issues,
    get_average_work_hours_by_user,
    get_week_work_hours_by_user,
)

# from libdatetime import (
#     date_is_in_last_seven_days,
#     get_last_day,
#     get_next_day,
#     Weekday,
# )

# from libworklogfilter import filter_component, filter_epic, filter_issuetype

if __name__ == "__main__":
    load_dotenv()

    jira = JIRA(
        os.environ["jira_site_url"],
        basic_auth=(os.environ["jira_api_email"], os.environ["jira_api_token"]),
    )

    sprint = get_sprint(jira)

    # pprint(jira.search_issues("issueType = 'Epic'")[1].raw)

    print(get_sprint_name(sprint=sprint))
    print(get_sprint_dates_str(sprint=sprint))
    print(get_sprint_goal(sprint=sprint))
    wl = get_all_worklogs_by_user(jira)
    pprint(get_week_work_hours_by_user(wl))
    pprint(get_average_work_hours_by_user(wl, start_date=datetime(2022, 5, 12)))

    # mip = sum_worklogs(wl["William Bruneau"], filter_epic(["MIP"]), jira=jira)
    # tot = sum_worklogs(wl["William Bruneau"], jira=jira)
    # pourc = (mip / tot) * 100
    # print(mip, tot, pourc)

    # print(get_user(jira, "Philippe Warren"))
    # print(get_all_issues(jira))
    # issues = get_all_issues(jira)
    # for issue in get_all_issues(jira):
    #     print(issue.key)
    #     pprint(issue.raw)
    #     break
    # print(wl["Philippe Warren"][0].raw)

    # wlf = filter(lambda x: date_is_in_last_seven_days(x.updated), wl["William Bruneau"])
    # pprint(list(wlf))
    # pprint(list(wl["William Bruneau"]))
    # print(get_all_worklogs_by_user(jira))

    # print(get_last_day(Weekday.Thursday))
    # print(get_next_day(Weekday.Thursday))

    # print(sum_worklogs(filter_worklog_for_week(wl["Philippe Warren"])))
    # print(
    #     sum_worklogs(
    #         wl["Philippe Warren"],
    #         lambda w, i: i.fields.issuetype.name in ("Admin"),
    #         jira=jira,
    #     )
    # )
    # print(
    #     sum_worklogs(
    #         wl["Philippe Warren"],
    #         filter_issuetype(("Admin",)),
    #         jira=jira,
    #     )
    # )
    # print(
    #     sum_worklogs(
    #         wl["Philippe Warren"],
    #         filter_component(("Cours",)),
    #         jira=jira,
    #     )
    # )
    # print(get_last_day(Weekday.Thursday, date=datetime(2022, 5, 26, 12)))
    # print(get_next_day(Weekday.Thursday, date=datetime(2022, 5, 26, 12)))
