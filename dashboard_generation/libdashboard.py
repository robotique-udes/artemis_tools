from jira import JIRA
from jira.client import ResultList
from jira.resources import Sprint, User, Issue, Worklog
from datetime import datetime
from collections import defaultdict

from typing import Iterable, cast, Callable

from libdatetime import (
    get_date,
    strip_leading_zero,
    get_last_day,
    get_next_day,
    Weekday,
)


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


def get_all_worklogs_by_user(jira: JIRA) -> dict[str, list[Worklog]]:
    d: defaultdict[str, list[Worklog]] = defaultdict(list)
    for issue in get_all_issues(jira):
        for worklog in jira.worklogs(issue.key):
            d[worklog.author.displayName].append(worklog)

    return dict(d)


def filter_worklog_for_week(worklogs: list[Worklog]) -> list[Worklog]:
    lower_bound = get_last_day(Weekday.Thursday)
    upper_bound = get_next_day(Weekday.Thursday)
    return [
        i
        for i in worklogs
        if get_date(i.updated) >= lower_bound and get_date(i.updated) < upper_bound
    ]


def get_all_worklogs_by_user_for_week(jira: JIRA) -> dict[str, list[Worklog]]:
    lower_bound = get_last_day(Weekday.Thursday)
    upper_bound = get_next_day(Weekday.Thursday)

    d: defaultdict[str, list[Worklog]] = defaultdict(list)
    for issue in get_all_issues(jira):
        for worklog in jira.worklogs(issue.key):
            if (
                get_date(worklog.updated) >= lower_bound
                and get_date(worklog.updated) < upper_bound
            ):
                d[worklog.author.displayName].append(worklog)

    return dict(d)


def sum_worklogs(
    worklogs: list[Worklog],
    predicate: Callable[[Worklog, Issue], bool] | None = None,
    jira: JIRA | None = None,
) -> float:
    if predicate is not None and jira is None:
        raise ValueError("Must provide `jira` when using `predicate`")

    predicate = predicate or (lambda x, y: True)

    def get_issue(worklog: Worklog) -> Issue | None:
        return jira.issue(worklog.issueId) if jira is not None else None

    return (
        sum(
            i.timeSpentSeconds
            for i in worklogs
            if predicate(i, cast(Issue, get_issue(i)))
        )
        / 3600
    )


def get_week_work_hours_by_user(
    wl: dict[str, list[Worklog]],
) -> dict[str, float]:

    d: dict[str, float] = {}
    for k, v in wl.items():
        d[k] = sum_worklogs(filter_worklog_for_week(v))

    return d


def get_average_work_hours_by_user(
    wl: dict[str, list[Worklog]],
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
