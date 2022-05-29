from jira.resources import Issue, Worklog

from typing import Callable, TypeAlias, Iterable

from types import SimpleNamespace


WorklogPredicate: TypeAlias = Callable[[Worklog, Issue], bool]


def filter_issuetype(issuetypes: Iterable[str]) -> WorklogPredicate:
    def pred(w: Worklog, i: Issue) -> bool:
        return i.fields.issuetype.name in issuetypes

    return pred


def filter_epic(epics: Iterable[str | None]) -> WorklogPredicate:
    def get_parent_epic(issue: Issue) -> Issue | SimpleNamespace:
        if issue.fields.issuetype.name == "Epic":
            return issue
        elif issue.fields.parent is not None:  # type: ignore
            return get_parent_epic(issue.fields.parent)  # type: ignore
        else:
            return SimpleNamespace(name=None)

    def pred(w: Worklog, i: Issue) -> bool:
        return get_parent_epic(i).name in epics

    return pred


def filter_component(components: Iterable[str | None]) -> WorklogPredicate:
    def pred(w: Worklog, i: Issue) -> bool:
        if i.fields.components == []:  # type: ignore
            return None in components

        c: set[str] = set(j.name for j in i.fields.components)  # type: ignore
        cp = set(components)
        return len(c & cp) > 0

    return pred
