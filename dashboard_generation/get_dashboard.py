#   get_dashboard.py
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
from dotenv import load_dotenv  # type: ignore
import os
from pathlib import Path

from datetime import datetime

from subprocess import call, DEVNULL

from concurrent.futures import ThreadPoolExecutor

from libdashboardjira import (
    get_sprint_name,
    get_sprint,
    get_sprint_for_next_week,
    get_sprint_dates_str,
    get_sprint_goal,
    get_all_worklogs_by_user,
    get_all_worklogs_by_issue,
    filter_worklog_for_week,
    get_all_issues,
    issues_by_key,
    get_tb_issue_yaml,
    get_work_hours_by_user_by_category,
    WorklogUser,
    get_all_worked_on_issue_from_worklogs,
    get_all_open_issues_in_sprints,
    get_all_epics_with_time_estimate_by_key,
    WorklogIssue,
)

from libdashboardlatex import (
    get_epic_advancements,
    get_block_questions,
    gen_latex,
    get_list_for_re_sub,
    get_risks,
    get_problems,
    get_budget,
    WorkedOnIssue,
    ToWorkOnIssue,
    get_to_work_on_issues,
    get_worked_on_issues,
    escape_latex,
)

from libdatetime import get_next_day, format_date, Weekday, format_date_file_postfix

from libdashboardyaml import DashboardConfig

from libdashboardgraph import generate_image

from PyPDF2 import PdfMerger

if __name__ == "__main__":
    load_dotenv()

    # as_date = datetime(2022, 7, 6)
    as_date = datetime.today()
    hour = 0

    jira = JIRA(
        os.environ["jira_site_url"],
        basic_auth=(os.environ["jira_api_email"], os.environ["jira_api_token"]),
        async_=True,
    )

    sprint = get_sprint(jira, date=as_date)

    cfg = DashboardConfig(
        get_tb_issue_yaml(jira, datetime=get_next_day(Weekday.Thursday, as_date, hour)),
        as_date=as_date,
    )

    iss = get_all_issues(jira)
    diss = issues_by_key(iss)
    dwliss = get_all_worklogs_by_issue(jira, diss)
    wl = get_all_worklogs_by_user(dwliss)

    all_wl: list[WorklogIssue] = []
    for user in wl:
        all_wl.extend(wl[user])

    depics = get_all_epics_with_time_estimate_by_key(jira=jira, issues_dict=diss)

    worked_on_issues = sorted(
        [
            WorkedOnIssue(i)
            for i in get_all_worked_on_issue_from_worklogs(
                filter_worklog_for_week(all_wl, as_date=as_date, hour=hour),
            )
        ],
        key=lambda i: i.status,
    )

    to_work_on_issues = sorted(
        [
            ToWorkOnIssue(i)
            for i in get_all_open_issues_in_sprints(
                iss,
                sprints={
                    get_sprint(jira, date=as_date),
                    get_sprint_for_next_week(jira, as_date=as_date, hour=hour),
                },
            )
        ],
        key=lambda x: x.assignee,
    )

    wl = get_work_hours_by_user_by_category(
        wl,
        start_date=datetime(2022, 5, 12),
        issues_dict=diss,
        as_date=as_date,
        hour=hour,
        categories={
            "tech": ["Story", "Tâche", "Test", "Bug"],
            "admin": ["Admin", "Financement", "TB"],
        },
    )

    wlu = [WorklogUser(k, v) for k, v in wl.items()]

    in_path = Path("dashboard_generation/PMC_Tableau_de_bord")
    out_path = Path("dashboard_generation/PMC_Tableau_de_bord_out")

    main_file = "main.tex"
    main_done_file = "main_fait.tex"
    main_todo_file = "main_a_faire.tex"
    image_hours_file = "images/heures.png"

    REPLACEMENTS: dict[str, str] = {
        r"@@SPRINT-NOM@@": escape_latex(get_sprint_name(sprint=sprint)),
        r"@@SPRINT-DATE@@": escape_latex(get_sprint_dates_str(sprint=sprint)),
        r"@@SPRINT-OBJECTIF@@": escape_latex(get_sprint_goal(sprint=sprint)),
        r"@@DATEHEURE-RENCONTRE@@": escape_latex(
            format_date(get_next_day(Weekday.Thursday, date=as_date))
        ),
        r"@@SUIVI-PRESENTATEUR@@": escape_latex(cfg.presentateur),
        r"@@RENCONTRE-PRESENTATEUR@@": escape_latex(cfg.presentateur),
        r"@@RENCONTRE-SECRETAIRE@@": escape_latex(cfg.secretaire),
        r"@@SUIVI-SUJETS@@": get_list_for_re_sub(cfg.sujets_suivi),
        r"@@ORDRE-JOUR@@": get_list_for_re_sub(cfg.ordre_du_jour),
        r"%\s+@@EPICS-AVANCEMENTS@@": get_epic_advancements(
            depics,
            filter=cfg.epic_filter,
        ),
        r"%\s+@@SEMAINE-RISQUES@@": get_risks(cfg.risques),
        r"%\s+@@SEMAINE-PROBLEMES@@": get_problems(cfg.problemes),
        r"%\s+@@BLOC-QUESTIONS@@": get_block_questions(cfg.questions),
        r"%\s+@@SEMAINE-FINANCES@@": get_budget(cfg.finances),
        r"@@SEMAINE-TACHES-FAITES@@": get_worked_on_issues(worked_on_issues),
        r"@@SEMAINE-TACHES-A-FAIRE@@": get_to_work_on_issues(to_work_on_issues),
    }

    generate_image(wlu, file=out_path / image_hours_file)

    gen_latex(
        REPLACEMENTS,
        ifile=in_path / main_file,
        ofile=out_path / main_file,
    )
    gen_latex(
        REPLACEMENTS,
        ifile=in_path / main_done_file,
        ofile=out_path / main_done_file,
    )
    gen_latex(
        REPLACEMENTS,
        ifile=in_path / main_todo_file,
        ofile=out_path / main_todo_file,
    )

    # input("Press Enter to continue...")

    latexmk_cmd = "latexmk -pdf -f -interaction=nonstopmode -outdir=../latex_gen"

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(
            call,
            f"{latexmk_cmd} {main_file}",
            stdout=DEVNULL,
            stderr=DEVNULL,
            cwd=out_path,
        )
        executor.submit(
            call,
            f"{latexmk_cmd} {main_done_file}",
            stdout=DEVNULL,
            stderr=DEVNULL,
            cwd=out_path,
        )
        executor.submit(
            call,
            f"{latexmk_cmd} {main_todo_file}",
            stdout=DEVNULL,
            stderr=DEVNULL,
            cwd=out_path,
        )

    merger = PdfMerger()
    merger.append(
        str(Path("dashboard_generation/latex_gen") / main_file.replace(".tex", ".pdf"))
    )
    merger.append(
        str(
            Path("dashboard_generation/latex_gen")
            / main_done_file.replace(".tex", ".pdf")
        )
    )
    merger.append(
        str(
            Path("dashboard_generation/latex_gen")
            / main_todo_file.replace(".tex", ".pdf")
        )
    )

    out_name = f"out/TB_Artemis_{format_date_file_postfix(get_next_day(Weekday.Thursday, date=as_date))}.pdf"

    merger.write(out_name)
