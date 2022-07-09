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
from bokeh.io import export_png, export_svg  # type: ignore
from bokeh.models import ColumnDataSource, FactorRange  # type: ignore

from libdashboardjira import WorklogUser
from libdatetime import compare_key
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

    nh = sorted(h, key=lambda x: compare_key(x.user.split()[-1]), reverse=True)

    tech: list[float] = []
    admin: list[float] = []
    other: list[float] = []
    avg: list[float] = []
    factors: list[tuple[str, str]] = []
    for i in nh:
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
        width=1800,
        height=900,
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

    font_size = "26pt"

    p.add_layout(p.legend[0], "above")  # type: ignore
    p.legend.orientation = "horizontal"
    p.yaxis.group_label_orientation = "horizontal"
    p.xaxis.axis_label_text_font_size = font_size
    p.xaxis.major_label_text_font_size = font_size
    p.yaxis.axis_label_text_font_size = font_size
    p.yaxis.major_label_text_font_size = font_size
    p.yaxis.group_text_font_size = font_size
    p.legend.title_text_font_size = "32pt"
    p.legend.label_text_font_size = "32pt"

    if file is not None:
        p.background_fill_color = None  # type: ignore
        p.border_fill_color = None  # type: ignore

        # Add chromedriver to PATH
        import chromedriver_binary  # type: ignore

        if str(file).lower().endswith(".svg"):
            export_svg(
                p,
                filename=file,
            )
        else:
            export_png(
                p,
                filename=file,
            )
    else:
        show(p)
