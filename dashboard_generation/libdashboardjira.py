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
from jira.resources import Sprint, User, Issue, Worklog
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

from typing import Iterable, cast
import re
from functools import partial

from concurrent.futures import ThreadPoolExecutor

from libissuefilter import (
    IssuePredicate,
    filter_issuetype,
    filter_epic,
    filter_and,
    filter_invert,
)

from libdatetime import (
    get_date,
    strip_leading_zero,
    get_last_day,
    get_next_day,
    Weekday,
    s_to_h,
)


@dataclass(frozen=True)
class WorklogIssue:
    wl: Worklog
    issue: Issue


@dataclass
class TimeEstimate:
    original_estimate: float
    remaining_estimate: float
    worked: float

    @staticmethod
    def from_issue(issue: Issue) -> "TimeEstimate":
        return TimeEstimate(
            original_estimate=s_to_h(issue.fields.timeoriginalestimate or 0.0),  # type: ignore
            remaining_estimate=s_to_h(issue.fields.timeestimate or 0.0),  # type: ignore
            worked=s_to_h(issue.fields.timespent or 0.0),  # type: ignore
        )

    @staticmethod
    def null() -> "TimeEstimate":
        return TimeEstimate(original_estimate=0.0, remaining_estimate=0.0, worked=0.0)

    @property
    def current_estimate(self) -> float:
        return self.remaining_estimate + self.worked

    @property
    def progress_percent(self) -> float:
        return (
            100 * self.worked / self.current_estimate
            if self.current_estimate > 0
            else 0.0
        )

    @property
    def ratio_percent(self) -> float:
        return (
            100 * self.worked / self.original_estimate
            if self.original_estimate > 0
            else -1.0
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
    jira: JIRA, as_date: datetime = datetime.today(), hour: int = 11
) -> Sprint:
    next_week = get_next_day(Weekday.Thursday, as_date, hour) + timedelta(days=1)
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


def issues_by_key(issues: list[Issue]) -> dict[str, Issue]:
    return {i.key: i for i in issues}


def get_all_epics(jira: JIRA) -> ResultList[Issue]:
    return cast(
        ResultList[Issue],
        jira.search_issues("project = Artemis and issuetype = Epic", maxResults=0),
    )


def get_all_epics_by_key(jira: JIRA) -> dict[str, Issue]:
    return {
        i.key: i
        for i in cast(
            ResultList[Issue],
            jira.search_issues("project = Artemis and issuetype = Epic", maxResults=0),
        )
    }


def add_time_estimate_to_epics(
    epics_dict: dict[str, Issue], epics_te_dict: dict[str, TimeEstimate]
) -> dict[str, tuple[Issue, TimeEstimate]]:
    ds: defaultdict[str, TimeEstimate] = defaultdict(
        lambda: TimeEstimate.null(), **epics_te_dict
    )
    return {k: (v, ds[k]) for k, v in epics_dict.items()}


def get_all_epics_with_time_estimate_by_key(
    jira: JIRA,
    issues_dict: dict[str, Issue],
) -> dict[str, tuple[Issue, TimeEstimate]]:
    depics = get_all_epics_by_key(jira)
    depics_te_sum = sum_time_estimate_by_epic(
        issues_dict=issues_dict, epics_dict=depics
    )
    return add_time_estimate_to_epics(depics, depics_te_sum)


def get_tb_issue(
    jira: JIRA, datetime: datetime = get_next_day(Weekday.Thursday)
) -> Issue:
    try:
        return jira.search_issues(f"project = Artemis and issuetype = TB and summary ~ 'TB {datetime.strftime('%Y/%m/%d')}'", maxResults=1)[0]  # type: ignore
    except IndexError:
        raise ValueError(f"No TB issue found for {datetime.strftime('%Y/%m/%d')}")


def get_tb_issue_yaml(
    jira: JIRA,
    datetime: datetime = get_next_day(Weekday.Thursday),
) -> str:
    issue = get_tb_issue(jira, datetime)
    return re.sub(
        r"\{code:yaml\}(.*)\{code\}",
        r"\1",
        issue.raw["fields"]["description"],
        flags=re.DOTALL,
    )


def get_worklogs_for_issue(
    issue: Issue,
    jira: JIRA,
) -> tuple[str, list[WorklogIssue]]:
    return issue.key, [WorklogIssue(wl, issue) for wl in jira.worklogs(issue.key)]


def get_all_worklogs_by_issue(
    jira: JIRA, issues_dict: dict[str, Issue]
) -> dict[str, list[WorklogIssue]]:
    d: dict[str, list[WorklogIssue]] = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        for k, d2 in executor.map(
            partial(get_worklogs_for_issue, jira=jira),
            issues_dict.values(),
        ):
            d[k] = d2

    return d


def get_all_worklogs_by_user(
    worklog_dict: dict[str, list[WorklogIssue]]
) -> dict[str, list[WorklogIssue]]:
    d: dict[str, list[WorklogIssue]] = defaultdict(list)

    for _, v in worklog_dict.items():
        for wli in v:
            d[wli.wl.author.displayName].append(wli)
    return d


def filter_worklog_for_week(
    worklogs: list[WorklogIssue], as_date: datetime = datetime.today(), hour: int = 11
) -> list[WorklogIssue]:
    lower_bound = get_last_day(Weekday.Thursday, as_date, hour)
    upper_bound = get_next_day(Weekday.Thursday, as_date, hour)
    return [
        i
        for i in worklogs
        if get_date(i.wl.started) >= lower_bound
        and get_date(i.wl.started) < upper_bound
    ]


def sum_worklogs(
    worklogs: list[WorklogIssue],
    predicate: IssuePredicate | None = None,
    issues_dict: dict[str, Issue] | None = None,
) -> float:
    if predicate is not None and issues_dict is None:
        raise ValueError("Must provide `issues_dict` when using `predicate`")

    predicate = predicate or (lambda x, y: True)

    return (
        sum(
            i.wl.timeSpentSeconds
            for i in worklogs
            if predicate(i.issue, cast(dict[str, Issue], issues_dict))
        )
        / 3600
    )


def sum_time_estimate_for_issues(
    issues_dict: dict[str, Issue],
    predicate: IssuePredicate | None = None,
) -> TimeEstimate:

    predicate = predicate or (lambda x, y: True)
    estimates = [
        TimeEstimate.from_issue(i)
        for i in issues_dict.values()
        if predicate(i, issues_dict)
    ]
    return TimeEstimate(
        original_estimate=sum(i.original_estimate for i in estimates),
        remaining_estimate=sum(i.remaining_estimate for i in estimates),
        worked=sum(i.worked for i in estimates),
    )


def sum_time_estimate_by_epic(
    issues_dict: dict[str, Issue],
    epics_dict: dict[str, Issue],
) -> dict[str, TimeEstimate]:
    d: dict[str, TimeEstimate] = {}

    for k, ep in epics_dict.items():
        d[k] = sum_time_estimate_for_issues(
            predicate=filter_and(
                (
                    filter_epic((ep.fields.summary,)),
                    filter_invert(filter_issuetype(("Epic",))),
                )
            ),
            issues_dict=issues_dict,
        )
    return d


def get_week_work_hours_by_user(
    wl: dict[str, list[WorklogIssue]],
    hour: int = 11,
) -> dict[str, float]:

    d: dict[str, float] = {}
    for k, v in wl.items():
        d[k] = sum_worklogs(filter_worklog_for_week(v, hour=hour))

    return d


def get_average_work_hours_by_user(
    wl: dict[str, list[WorklogIssue]],
    start_date: datetime,
    hour: int = 11,
) -> dict[str, float]:

    d: dict[str, float] = {}
    for k, v in wl.items():
        d[k] = sum_worklogs(v) / (
            (
                get_next_day(Weekday.Thursday, hour=hour)
                - get_last_day(Weekday.Thursday, start_date, hour=hour)
            ).days
            / 7
        )

    return d


def get_work_hours_by_user_by_category(
    wl: dict[str, list[WorklogIssue]],
    start_date: datetime,
    issues_dict: dict[str, Issue],
    categories: dict[str, Iterable[str]] | None = None,
    as_date: datetime = datetime.today(),
    hour: int = 11,
) -> dict[str, dict[str, float]]:

    if categories is None:
        categories = {
            "tech": ["Story", "Tâche", "Bug", "Test"],
            "admin": ["Admin", "Livrable", "Financement", "TB"],
        }

    d: dict[str, dict[str, float]] = defaultdict(dict)
    for k, v in wl.items():
        for category, issue_types in categories.items():
            d[k][category] = sum_worklogs(
                filter_worklog_for_week(v, as_date=as_date, hour=hour),
                filter_issuetype(issue_types),
                issues_dict=issues_dict,
            )

        d[k]["other"] = sum_worklogs(
            filter_worklog_for_week(v, as_date=as_date, hour=hour)
        )
        for category in categories.keys():
            d[k]["other"] -= d[k][category]

        d[k]["avg"] = sum_worklogs(v) / (
            (
                get_next_day(Weekday.Thursday, as_date, hour)
                - get_last_day(Weekday.Thursday, start_date, hour)
            ).days
            / 7
        )
        d[k]["avg_rolling"] = sum_worklogs(v) / (
            (
                as_date.astimezone() - get_last_day(Weekday.Thursday, start_date, hour)
            ).days
            / 7
        )

    return d


def get_average_work_hours_by_user_rolling(
    wl: dict[str, list[WorklogIssue]],
    start_date: datetime,
    hour: int = 11,
) -> dict[str, float]:

    d: dict[str, float] = {}
    for k, v in wl.items():
        d[k] = sum_worklogs(v) / (
            (
                datetime.today().astimezone()
                - get_last_day(Weekday.Thursday, start_date, hour=hour)
            ).days
            / 7
        )

    return d


def get_all_worked_on_issue_from_worklogs(worklogs: list[WorklogIssue]) -> set[Issue]:
    return {i.issue for i in worklogs}


def get_all_open_issues_in_sprints(
    issues: list[Issue], sprints: Iterable[Sprint]
) -> set[Issue]:
    sprints_ids = {s.id for s in sprints}

    return {
        i
        for i in issues
        if (
            sprints_ids & {j.id for j in (cast(list[Sprint], i.fields.customfield_10020) or [])}  # type: ignore
            != set()
            and not "[TODO_AUTO]" in i.fields.summary
        )
        and i.fields.status.statusCategory.name != "Terminé"
    }
