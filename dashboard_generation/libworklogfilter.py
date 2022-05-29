#   libworklogfilter.py
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
