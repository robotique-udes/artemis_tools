#   libdashboardgraph.py
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

from bokeh.plotting import figure, show  # type: ignore
from bokeh.io import export_png  # type: ignore
from bokeh.models import ColumnDataSource, FactorRange  # type: ignore

from libdashboardjira import WorklogUser
from pathlib import Path

from enum import Enum


class COLORS(Enum):
    Tech = "blue"
    Admin = "orange"
    Other = "red"
    Avg = "gray"


class LABELS(Enum):
    Tech = "Technique"
    Admin = "Admin"
    Other = "Autre"
    Avg = "Moyenne"


def generate_image(h: list[WorklogUser], file: Path | None = None) -> None:

    stackers = [
        LABELS.Tech.value,
        LABELS.Admin.value,
        LABELS.Other.value,
        LABELS.Avg.value,
    ]

    tech: list[float] = []
    admin: list[float] = []
    other: list[float] = []
    avg: list[float] = []
    factors: list[tuple[str, str]] = []
    for i in h:
        factors.append((i.user, "Moyenne"))
        factors.append((i.user, "Semaine"))
        tech.append(0.0)
        tech.append(i.tech)
        admin.append(0.0)
        admin.append(i.admin)
        other.append(0.0)
        other.append(i.other)
        avg.append(i.avg)
        avg.append(0.0)

    source = ColumnDataSource(
        data=dict(
            x=factors,
            Technique=tech,
            Autre=other,
            Admin=admin,
            Moyenne=avg,
        )
    )

    colors = [
        COLORS.Tech.value,
        COLORS.Admin.value,
        COLORS.Other.value,
        COLORS.Avg.value,
    ]

    p = figure(
        y_range=FactorRange(*factors),
        x_axis_label="Temps (h)",
        width=600,
        height=400,
        toolbar_location=None,
    )
    p.hbar_stack(  # type: ignore
        stackers,
        y="x",
        height=0.9,
        color=colors,
        source=source,
        legend_label=stackers,
    )

    p.add_layout(p.legend[0], "above")  # type: ignore
    p.legend.orientation = "horizontal"
    p.yaxis.group_label_orientation = "horizontal"

    if file is not None:
        p.background_fill_color = None  # type: ignore
        p.border_fill_color = None  # type: ignore
        try:
            export_png(p, filename=file)
        except RuntimeError:
            print(
                "Can't run export_png: install chromedriver using `python -m selenium-chromedriver`"
            )

    else:
        show(p)
