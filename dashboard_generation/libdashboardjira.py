#   libdashboardjira.py
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
from jira.client import ResultList
from jira.resources import Sprint, User, Issue
from datetime import datetime, timedelta
from collections import defaultdict

from typing import Iterable, cast
import re
from pprint import pprint

from libworklogfilter import WorklogPredicate, filter_issuetype, WorklogIssue

from libdatetime import (
    get_date,
    strip_leading_zero,
    get_last_day,
    get_next_day,
    Weekday,
)


class WorklogUser:
    def __init__(self, name: str, wl: dict[str, float]):
        self.user = name
        self.wl = wl
        self.tech = wl["tech"]
        self.admin = wl["admin"]
        self.other = wl["other"]
        self.avg = wl["avg"]
        self.avg_rolling = wl["avg_rolling"]

    def __repr__(self) -> str:
        return f"{self.user}: {self.wl})"


def get_sprint(jira: JIRA, date: datetime = datetime.today()) -> Sprint:
    sprints: Iterable[Sprint] = jira.sprints(
        board_id="1",
    )

    date = date.astimezone()

    return [
        i
        for i in sprints
        if get_date(i.startDate) <= date and get_date(i.endDate) >= date
    ][0]


def get_next_sprint(jira: JIRA, date: datetime = datetime.today()) -> Sprint:
    sprints: Iterable[Sprint] = jira.sprints(
        board_id="1",
    )

    date = date.astimezone()

    return [i for i in sprints if get_date(i.startDate) >= date][0]


def get_sprint_for_next_week(
    jira: JIRA, as_date: datetime = datetime.today()
) -> Sprint:
    next_week = get_next_day(Weekday.Thursday, as_date) + timedelta(days=1)
    return get_sprint(jira, date=next_week)


def get_sprint_name(
    *,
    jira: JIRA | None = None,
    sprint: Sprint | None = None,
    date: datetime = datetime.today(),
) -> str:
    if (jira is None and sprint is None) or (jira is not None and sprint is not None):
        raise ValueError("Must provide either `jira` or `sprint`")

    if jira is not None:
        sprint = get_sprint(jira, date)

    sprint = cast(Sprint, sprint)

    return sprint.name


def get_sprint_dates(
    *,
    jira: JIRA | None = None,
    sprint: Sprint | None = None,
    date: datetime = datetime.today(),
) -> tuple[datetime, datetime]:
    if (jira is None and sprint is None) or (jira is not None and sprint is not None):
        raise ValueError("Must provide either `jira` or `sprint`")

    if jira is not None:
        sprint = get_sprint(jira, date)

    sprint = cast(Sprint, sprint)

    return (
        get_date(sprint.startDate),
        get_date(sprint.endDate),
    )


def get_sprint_dates_str(
    *,
    jira: JIRA | None = None,
    sprint: Sprint | None = None,
    date: datetime = datetime.today(),
) -> str:
    dates = get_sprint_dates(
        jira=jira,
        sprint=sprint,
        date=date,
    )

    return f"{strip_leading_zero(dates[0].strftime('%d %B'))} au {strip_leading_zero(dates[1].strftime('%d %B %Y'))}"


def get_sprint_goal(
    *,
    jira: JIRA | None = None,
    sprint: Sprint | None = None,
    date: datetime = datetime.today(),
) -> str:
    if (jira is None and sprint is None) or (jira is not None and sprint is not None):
        raise ValueError("Must provide either `jira` or `sprint`")

    if jira is not None:
        sprint = get_sprint(jira, date)

    sprint = cast(Sprint, sprint)

    return sprint.goal


def get_user(jira: JIRA, name: str) -> User:
    return jira.search_users(query=name, maxResults=1)[0]


def get_all_issues(jira: JIRA) -> ResultList[Issue]:
    return cast(
        ResultList[Issue],
        jira.search_issues("project = Artemis", maxResults=0),
    )


def get_all_epics(jira: JIRA) -> ResultList[Issue]:
    return cast(
        ResultList[Issue],
        jira.search_issues("project = Artemis and issuetype = Epic", maxResults=0),
    )


def get_tb_issue(
    jira: JIRA, datetime: datetime = get_next_day(Weekday.Thursday)
) -> Issue:
    try:
        return jira.search_issues(f"project = Artemis and issuetype = TB and summary ~ 'TB {datetime.strftime('%Y/%m/%d')}'", maxResults=1)[0]  # type: ignore
    except IndexError:
        raise ValueError(f"No TB issue found for {datetime.strftime('%Y/%m/%d')}")


def get_tb_issue_yaml_assignee(
    jira: JIRA, datetime: datetime = get_next_day(Weekday.Thursday)
) -> tuple[str, str]:
    issue = get_tb_issue(jira, datetime)
    return (
        re.sub(
            r"\{code:yaml\}(.*)\{code\}",
            r"\1",
            issue.raw["fields"]["description"],
            flags=re.DOTALL,
        ),
        issue.fields.assignee.displayName,  # type: ignore
    )


def get_all_worklogs_by_user(jira: JIRA) -> dict[str, list[WorklogIssue]]:
    d: defaultdict[str, list[WorklogIssue]] = defaultdict(list)
    for issue in get_all_issues(jira):
        for worklog in jira.worklogs(issue.key):
            d[worklog.author.displayName].append(WorklogIssue(worklog, issue))

    return dict(d)


def filter_worklog_for_week(
    worklogs: list[WorklogIssue], as_date: datetime = datetime.today()
) -> list[WorklogIssue]:
    lower_bound = get_last_day(Weekday.Thursday, as_date)
    upper_bound = get_next_day(Weekday.Thursday, as_date)
    return [
        i
        for i in worklogs
        if get_date(i.wl.started) >= lower_bound
        and get_date(i.wl.started) < upper_bound
    ]


def get_all_worklogs_by_user_for_week(jira: JIRA) -> dict[str, list[WorklogIssue]]:
    lower_bound = get_last_day(Weekday.Thursday)
    upper_bound = get_next_day(Weekday.Thursday)

    d: defaultdict[str, list[WorklogIssue]] = defaultdict(list)
    for issue in get_all_issues(jira):
        for worklog in jira.worklogs(issue.key):
            if (
                get_date(worklog.started) >= lower_bound
                and get_date(worklog.started) < upper_bound
            ):
                d[worklog.author.displayName].append(WorklogIssue(worklog, issue))

    return dict(d)


def sum_worklogs(
    worklogs: list[WorklogIssue],
    predicate: WorklogPredicate | None = None,
    jira: JIRA | None = None,
) -> float:
    if predicate is not None and jira is None:
        raise ValueError("Must provide `jira` when using `predicate`")

    predicate = predicate or (lambda x, y: True)

    # def get_issue(worklog: Worklog) -> Issue | None:
    #     return jira.issue(worklog.issueId) if jira is not None else None

    return (
        # sum(i.timeSpentSeconds for i in worklogs if predicate(i, cast(JIRA, jira)))
        sum(i.wl.timeSpentSeconds for i in worklogs if predicate(i, cast(JIRA, jira)))
        / 3600
    )


def get_week_work_hours_by_user(
    wl: dict[str, list[WorklogIssue]],
) -> dict[str, float]:

    d: dict[str, float] = {}
    for k, v in wl.items():
        d[k] = sum_worklogs(filter_worklog_for_week(v))

    return d


def get_average_work_hours_by_user(
    wl: dict[str, list[WorklogIssue]],
    start_date: datetime,
) -> dict[str, float]:

    d: dict[str, float] = {}
    for k, v in wl.items():
        d[k] = sum_worklogs(v) / (
            (
                get_next_day(Weekday.Thursday)
                - get_last_day(Weekday.Thursday, start_date)
            ).days
            / 7
        )

    return d


def get_work_hours_by_user_by_category(
    wl: dict[str, list[WorklogIssue]],
    start_date: datetime,
    jira: JIRA,
    categories: dict[str, Iterable[str]] | None = None,
    as_date: datetime = datetime.today(),
) -> dict[str, dict[str, float]]:

    if categories is None:
        categories = {
            "tech": ["Story", "Tâche", "Bug", "Test"],
            "admin": ["Admin", "Livrable", "Financement", "Réunion"],
        }

    d: dict[str, dict[str, float]] = defaultdict(dict)
    for k, v in wl.items():
        for category, issue_types in categories.items():
            d[k][category] = sum_worklogs(
                filter_worklog_for_week(v, as_date=as_date),
                filter_issuetype(issue_types),
                jira=jira,
            )

        d[k]["other"] = sum_worklogs(filter_worklog_for_week(v, as_date=as_date))
        for category in categories.keys():
            d[k]["other"] -= d[k][category]

        d[k]["avg"] = sum_worklogs(v) / (
            (
                get_next_day(Weekday.Thursday, as_date)
                - get_last_day(Weekday.Thursday, start_date)
            ).days
            / 7
        )
        d[k]["avg_rolling"] = sum_worklogs(v) / (
            (as_date.astimezone() - get_last_day(Weekday.Thursday, start_date)).days / 7
        )

    return d


def get_average_work_hours_by_user_rolling(
    wl: dict[str, list[WorklogIssue]],
    start_date: datetime,
) -> dict[str, float]:

    d: dict[str, float] = {}
    for k, v in wl.items():
        d[k] = sum_worklogs(v) / (
            (
                datetime.today().astimezone()
                - get_last_day(Weekday.Thursday, start_date)
            ).days
            / 7
        )

    return d


def get_all_worked_on_issue_from_worklogs(
    worklogs: list[WorklogIssue], sprint: Sprint
) -> set[Issue]:
    return {
        i.issue
        for i in worklogs
        # if sprint.id
        # in (
        #     j.id
        #     for j in (
        #         cast(
        #             list[Sprint], i.issue.fields.customfield_10020 or []  # type:ignore
        #         )
        #     )
        # )
    }


def get_all_open_issues_in_sprint(issues: list[Issue], sprint: Sprint) -> set[Issue]:
    return {
        i
        for i in issues
        if sprint.id
        in (
            j.id for j in (cast(list[Sprint], i.fields.customfield_10020) or [])  # type: ignore
        )
        and i.fields.status.statusCategory.name == "En cours"
    }
