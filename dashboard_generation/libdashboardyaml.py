#   libdashboardyaml.py
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

from ruamel.yaml import YAML
from typing import Any
from libdashboardlatex import Risk, Problem, Budget, MemberStandup

from datetime import datetime

from libdatetime import compare_key

yaml = YAML(pure=True)


class DashboardConfig:
    def __init__(self, text: str, as_date: datetime = datetime.today()) -> None:
        self.config: dict[str, Any] = yaml.load(text)  # type: ignore
        self.as_date = as_date

    @property
    def epic_filter(self) -> list[str]:
        return self.config["epic"]

    @property
    def presentateur(self) -> str:
        return self.config["presentateur"]

    @property
    def secretaire(self) -> str:
        return self.config["secretaire"]

    @property
    def ordre_du_jour(self) -> list[str]:
        return self.config["ordre_du_jour"]

    @property
    def risques(self) -> list[Risk]:
        return [
            Risk(name=i["nom"], level=i["niveau"], mitigation=i["mitigation"])
            for i in self.config["risques"]
        ]

    @property
    def problemes(self) -> list[Problem]:
        return [
            Problem(
                name=i["nom"],
                resolved=i["resolu"],
                solution=i["solution"],
            )
            for i in self.config["problemes"]
        ]

    @property
    def questions(self) -> list[str] | None:
        return self.config["questions"] if "questions" in self.config else None

    @property
    def sujets_suivi(self) -> list[str]:
        return self.config["sujets_suivi"]

    @property
    def finances(self) -> list[Budget]:
        return [
            Budget(
                date=i["date"],
                item=i["item"],
                montant=i["montant"],
                solde=i["solde"],
                as_date=self.as_date,
            )
            for i in self.config["budget"]
        ]

    @property
    def tour_de_table(self) -> list[MemberStandup]:
        return sorted(
            [
                MemberStandup(
                    name=i["nom"],
                    work_done=i["fait"],
                    work_to_do=i["a_faire"],
                    important=i["important"] if "important" in i else "",
                )
                for i in self.config["tour_de_table"]
            ],
            key=lambda x: compare_key(x.name.split()[-1]),
        )
