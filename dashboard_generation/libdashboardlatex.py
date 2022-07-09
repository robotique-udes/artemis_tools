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

import re
from pathlib import Path

from datetime import datetime

from typing import Iterable

from libdashboardjira import (
    TimeEstimate,
)

from libdatetime import s_to_h


def escape_latex(text: str) -> str:
    SPECIAL_CHARACTERS = "&%$#_{}"
    text = text.replace("\\", "\\\\textbackslash")
    text = text.replace("~", "\\\\textasciitilde")
    text = text.replace("^", "\\\\textasciicircum")
    for c in SPECIAL_CHARACTERS:
        text = text.replace(c, f"\\\\{c}")
    return text


def format_progress(progress: float) -> str:
    if progress == 0:
        return f"\\\\cellcolor{{red}}{progress:.0f}\\\\%"
    elif progress > 0 and progress <= 100 * 2 / 3:
        return f"\\\\cellcolor{{orange}}{progress:.0f}\\\\%"
    elif progress > 100 * 2 / 3 and progress < 100:
        return f"\\\\cellcolor{{yellow}}{progress:.0f}\\\\%"
    elif progress == 100:
        return f"\\\\cellcolor{{green}}{progress:.0f}\\\\%"
    else:
        return f"{progress:.0f}\\\\%"


class Risk:
    @staticmethod
    def color_map(level: int) -> str:
        if level >= 3:
            return "\\\\cellcolor{green}"
        elif level == 2:
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


class Budget:
    @staticmethod
    def format_cash(value: float) -> str:
        return f"\\\\SI{{{value:.2f}}}{{\\\\$}}"

    def format_solde(self) -> str:
        if self.solde < 0:
            return f"\\\\cellcolor{{red}}{Budget.format_cash(self.solde)}"
        else:
            return Budget.format_cash(self.solde)

    def format_montant(self) -> str:
        return Budget.format_cash(self.montant) if self.montant else "--"

    def __init__(
        self,
        date: str | None,
        item: str | None,
        montant: float | None,
        solde: float,
        as_date: datetime = datetime.today(),
    ) -> None:
        self.date = date or as_date.astimezone().strftime("%m/%d")
        self.item = item
        self.montant = montant
        self.solde = solde

    def __str__(self) -> str:
        return f"{escape_latex(self.date)} & {escape_latex(self.item or '--')} & {self.format_montant()} & {self.format_solde()} \\\\\\\\ \\\\hline"


class Epic:
    def format_ratio(self) -> str:
        ratio = self.te.ratio_percent
        if ratio <= -1:
            return "-"
        elif ratio <= 100 * 2 / 3 and self.te.progress_percent == 100:
            return f"\\\\cellcolor{{orange}}{ratio:.0f}\\\\%"
        elif ratio >= 100 * 3 / 2:
            return f"\\\\cellcolor{{orange}}{ratio:.0f}\\\\%"
        else:
            return f"{ratio:.0f}\\\\%"

    def __init__(self, epic: Issue, time_estimate: TimeEstimate) -> None:
        self.epic = epic
        self.name = epic.fields.summary
        self.key = epic.key
        self.duedate = epic.fields.duedate
        self.assignee: str = epic.fields.assignee.displayName if epic.fields.assignee else ""  # type: ignore

        self.te = time_estimate
        self.te.original_estimate = s_to_h(epic.fields.timeoriginalestimate or 0.0)  # type: ignore

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {escape_latex(self.assignee)} & {self.te.original_estimate:.0f} & {self.te.current_estimate:.0f} & {format_progress(self.te.progress_percent)} & {self.format_ratio()} \\\\\\\\ \\\\hline"


class WorkedOnIssue:
    def format_ratio(self) -> str:
        ratio = self.ratio
        if ratio <= -1:
            return "-"
        elif ratio <= 100 * 2 / 3 and self.status == "Terminé":
            return f"\\\\cellcolor{{orange}}{ratio:.0f}\\\\%"
        elif ratio >= 100 * 3 / 2:
            return f"\\\\cellcolor{{red}}{ratio:.0f}\\\\%"
        else:
            return f"{ratio:.0f}\\\\%"

    def format_status(self) -> str:
        status = self.status
        if status == "A faire":
            return f"\\\\cellcolor{{red}}À faire"
        elif status == "En cours":
            return f"\\\\cellcolor{{yellow}}{escape_latex(status)}"
        elif status == "Terminé":
            return f"\\\\cellcolor{{green}}{escape_latex(status)}"
        else:
            return f"{escape_latex(status)}"

    def __init__(self, issue: Issue) -> None:
        self.issue = issue
        self.name = issue.fields.summary
        self.status = issue.fields.status.statusCategory.name
        self.assignee = (
            issue.fields.assignee.displayName if issue.fields.assignee else ""
        )
        self.original_estimate = s_to_h(issue.fields.timeoriginalestimate or 0.0)  # type: ignore
        self.remaining_estimate = s_to_h(issue.fields.timeestimate or 0.0)  # type: ignore
        self.worked = s_to_h(issue.fields.timespent or 0.0)  # type: ignore
        try:
            self.progress: int = issue.fields.progress.percent  # type: ignore
        except AttributeError:
            self.progress = 0
        self.ratio = 100 * self.worked / self.original_estimate if self.original_estimate != 0 else -1  # type: ignore

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {self.format_status()} & {escape_latex(self.assignee)} & {self.original_estimate:.1f} & {self.remaining_estimate:.1f} & {self.worked:.1f} & {format_progress(self.progress)} & {self.format_ratio()} \\\\\\\\ \\\\hline"


class ToWorkOnIssue:
    def __init__(self, issue: Issue) -> None:
        self.issue = issue
        self.name = issue.fields.summary
        self.assignee = (
            issue.fields.assignee.displayName if issue.fields.assignee else ""
        )
        self.remaining_estimate = s_to_h(issue.fields.timeestimate or 0.0)  # type: ignore
        try:
            self.progress: int = issue.fields.progress.percent  # type: ignore
        except AttributeError:
            self.progress = 0

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {escape_latex(self.assignee)} & {self.remaining_estimate:.1f} & {format_progress(self.progress)} \\\\\\\\ \\\\hline"


class MemberStandup:
    def __init__(
        self, name: str, work_done: str, work_to_do: str, important: str
    ) -> None:
        self.name = name
        self.work_done = work_done
        self.work_to_do = work_to_do
        self.important = important

    def __str__(self) -> str:
        return f"{escape_latex(self.name)} & {escape_latex(self.work_done)} & {escape_latex(self.work_to_do)} & \\\\textbf{{{escape_latex(self.important)}}} \\\\\\\\ \\\\hline"


def get_epic_advancements(
    epics: dict[str, tuple[Issue, TimeEstimate]], filter: Iterable[str]
) -> str:
    return "\n".join(
        str(Epic(epic, te))  # type: ignore
        for epic, te in sorted(epics.values(), key=lambda x: x[0].fields.summary)  # type: ignore
        if any(f.lower() in Epic(epic, te).name.lower() for f in filter)  # type: ignore
    )


def get_risks(risks: list[Risk]) -> str:
    return "\n".join(str(risk) for risk in risks)


def get_problems(problems: list[Problem]) -> str:
    return "\n".join(str(problem) for problem in problems)


def get_budget(budget: list[Budget]) -> str:
    return "\n".join(str(b) for b in budget)


def get_to_work_on_issues(issues: list[ToWorkOnIssue]) -> str:
    return "\n".join(str(issue) for issue in issues)


def get_worked_on_issues(issues: list[WorkedOnIssue]) -> str:
    return "\n".join(str(issue) for issue in issues)


def get_standup(standup: list[MemberStandup]) -> str:
    return "\n".join(str(member) for member in standup)


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
