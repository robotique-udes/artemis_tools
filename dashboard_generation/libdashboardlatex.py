#   libdashboardlatex.py
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

from jira.resources import Issue
from jira import JIRA

import re
from pathlib import Path

from typing import Iterable

from libdashboardjira import (
    get_all_epics,
)


def escape_latex(text: str) -> str:
    SPECIAL_CHARACTERS = "&%$#_{}"
    text = text.replace("\\", "\\\\textbackslash")
    text = text.replace("~", "\\\\textasciitilde")
    text = text.replace("^", "\\\\textasciicircum")
    for c in SPECIAL_CHARACTERS:
        text = text.replace(c, f"\\\\{c}")
    return text


def s_to_h(seconds: int) -> float:
    return seconds / 3600


class Risk:
    @staticmethod
    def color_map(level: int) -> str:
        if level <= 3:
            return "\\\\cellcolor{green}"
        elif level <= 5:
            return "\\\\cellcolor{yellow}"
        else:
            return "\\\\cellcolor{red}"

    def __init__(self, name: str, level: int, mitigation: str) -> None:
        self.name = name
        self.level = level
        self.mitigation = mitigation
        self.color = Risk.color_map(level)

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {self.color}{self.level} & {escape_latex(self.mitigation)} \\\\\\\\ \\\\hline"


class Problem:
    def __init__(self, name: str, resolved: bool, solution: str) -> None:
        self.name = name
        self.resolved = resolved
        self.solution = solution

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {'Oui' if self.resolved else 'Non'} & {escape_latex(self.solution)} \\\\\\\\ \\\\hline"


class Epic:
    def __init__(self, epic: Issue) -> None:
        self.epic = epic
        self.name = epic.fields.summary
        self.key = epic.key
        self.duedate = epic.fields.duedate
        self.assignee: str = epic.fields.assignee.displayName if epic.fields.assignee else ""  # type: ignore
        self.progress: int = s_to_h(epic.fields.aggregateprogress.progress)  # type: ignore
        self.estimate: int = s_to_h(epic.fields.aggregateprogress.total)  # type: ignore
        try:
            self.percent: int = epic.fields.aggregateprogress.percent  # type: ignore
        except AttributeError:
            self.percent = 0

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {escape_latex(self.assignee)} & {self.estimate:.0f} & {self.progress:.0f} & {self.percent:.0f}\\\\% \\\\\\\\ \\\\hline"


class WorkedOnIssue:
    @staticmethod
    def format_ratio(ratio: float) -> str:
        if ratio <= -1:
            return "-"
        elif ratio >= 150:
            return f"\\\\cellcolor{{red}}{ratio:.0f}\\\\%"
        else:
            return f"{ratio:.0f}\\\\%"

    def __init__(self, issue: Issue) -> None:
        self.issue = issue
        self.name = issue.fields.summary
        self.status = issue.fields.status.statusCategory.name
        self.assignee = (
            issue.fields.assignee.displayName if issue.fields.assignee else ""
        )
        self.original_estimate = s_to_h(issue.fields.timeoriginalestimate or 0)  # type: ignore
        self.remaining_estimate = s_to_h(issue.fields.timeestimate or 0)  # type: ignore
        self.worked = s_to_h(issue.fields.timespent or 0)  # type: ignore
        self.ratio = 100 * self.worked / self.original_estimate if self.original_estimate != 0 else -1  # type: ignore

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {escape_latex(self.status)} & {escape_latex(self.assignee)} & {self.original_estimate:.1f} & {self.remaining_estimate:.1f} & {self.worked:.1f} & {self.format_ratio(self.ratio)} \\\\\\\\ \\\\hline"


class ToWorkOnIssue:
    def __init__(self, issue: Issue) -> None:
        self.issue = issue
        self.name = issue.fields.summary
        self.assignee = (
            issue.fields.assignee.displayName if issue.fields.assignee else ""
        )
        self.remaining_estimate = s_to_h(issue.fields.timeestimate or 0)  # type: ignore

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {escape_latex(self.assignee)} & {self.remaining_estimate:.1f} \\\\\\\\ \\\\hline"


def get_epic_advancements(jira: JIRA, filter: Iterable[str]) -> str:
    return "\n".join(
        str(Epic(epic))  # type: ignore
        for epic in sorted(get_all_epics(jira), key=lambda x: x.fields.summary)  # type: ignore
        if any(f in Epic(epic).name for f in filter)  # type: ignore
    )


def get_risks(risks: list[Risk]) -> str:
    return "\n".join(str(risk) for risk in risks)


def get_problems(problems: list[Problem]) -> str:
    return "\n".join(str(problem) for problem in problems)


def get_to_work_on_issues(issues: list[ToWorkOnIssue]) -> str:
    return "\n".join(str(issue) for issue in issues)


def get_worked_on_issues(issues: list[WorkedOnIssue]) -> str:
    return "\n".join(str(issue) for issue in issues)


def get_list_for_re_sub(items: list[str]) -> str:
    return "\\n".join("\\\\item " + f"{escape_latex(item)}" for item in items)


def get_block_questions(questions: list[str] | None) -> str:
    if questions is None:
        return ""

    s = (
        """\\\\block{Questions}
    {
        \\\\begin{enumerate}\\n"""
        + "\\n".join(
            ("\\\\item " + f"{escape_latex(question)}") for question in questions
        )
        + """
        \\\\end{enumerate}
    }"""
    )
    return s


def gen_latex(replacements: dict[str, str], ifile: Path, ofile: Path) -> None:
    with Path(ifile).expanduser().resolve().open("r", encoding="utf-8") as input_file:
        with Path(ofile).expanduser().resolve().open(
            "w", encoding="utf-8"
        ) as output_file:
            for line in input_file:
                for key, value in replacements.items():
                    line = re.sub(key, value, line)

                output_file.write(line)
