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


from typing import Callable, TypeAlias, Iterable
from jira.resources import Issue

from types import SimpleNamespace


IssuePredicate: TypeAlias = Callable[[Issue, dict[str, Issue]], bool]


def filter_invert(pred: IssuePredicate) -> IssuePredicate:
    def pred_inv(i: Issue, id: dict[str, Issue]) -> bool:
        return not pred(i, id)

    return pred_inv


def filter_issuetype(issuetypes: Iterable[str]) -> IssuePredicate:
    def get_parent_issuetype(issue: Issue, issues_dict: dict[str, Issue]) -> str:
        if (
            issue.fields.issuetype.subtask is True
            or issue.fields.issuetype.name == "Sous-tâche"
        ):
            try:
                if issue.fields.parent is not None:  # type: ignore
                    parent = issues_dict[issue.fields.parent.key]  # type: ignore
                    return get_parent_issuetype(parent, issues_dict)  # type: ignore
                else:
                    raise AttributeError("Sub-task has no parent")
            except AttributeError:
                raise AttributeError("Sub-task has no parent")
        else:
            return issue.fields.issuetype.name

    def pred(i: Issue, id: dict[str, Issue]) -> bool:
        return get_parent_issuetype(i, id) in issuetypes

    return pred


def filter_epic(epics: Iterable[str | None]) -> IssuePredicate:
    def get_parent_epic(
        issue: Issue, issues_dict: dict[str, Issue]
    ) -> Issue | SimpleNamespace:
        if issue.fields.issuetype.name == "Epic":
            return issue

        try:
            if issue.fields.parent is not None:  # type: ignore
                parent = issues_dict[issue.fields.parent.key]  # type: ignore
                return get_parent_epic(parent, issues_dict)  # type: ignore
            else:
                return SimpleNamespace(fields=SimpleNamespace(summary=None))
        except AttributeError:
            return SimpleNamespace(fields=SimpleNamespace(summary=None))

    def pred(i: Issue, id: dict[str, Issue]) -> bool:
        return get_parent_epic(i, id).fields.summary in epics

    return pred


def filter_component(components: Iterable[str | None]) -> IssuePredicate:
    def pred(i: Issue, id: dict[str, Issue]) -> bool:
        if i.fields.components == []:  # type: ignore
            return None in components

        c: set[str] = set(j.name for j in i.fields.components)  # type: ignore
        cp = set(components)
        return len(c & cp) > 0

    return pred
