"""Generate the synthetic T0 fixture set: six course pages, two nights.

day0 is the baseline. day1 carries exactly five planted changes:

  1. moved      data-structures   Midterm 1: Oct 14, 11:00 AM -> Oct 16, 11:00 AM
  2. added      linear-algebra    Problem Set 5, due Nov 6 by 11:59 PM
  3. removed    physics-1         Lab Report 2 (due Oct 9 by 5:00 PM) disappears
  4. reworded   writing-seminar   "Essay 1 draft" -> "Essay 1: first draft", same date
  5. unreadable microeconomics    page replaced with an empty file (failed load)

modern-history is the control: identical content, different page noise.

Every page also carries noise that changes between nights and must never show
up in a diff: a generated-at footer timestamp, session ids in nav links,
"posted N hours ago" meta spans, and a "last visited" banner.

Run:  python -m vidya.fixtures.build
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_URL = "https://lms.example.edu"

COURSES: dict[str, dict] = {
    "data-structures": {
        "name": "CS 201 Data Structures", "ou": "41001",
        "announcements": [
            ("Welcome to CS 201", "2026-09-01", "Welcome! Read the syllabus before our first lecture."),
            ("Office hours", "2026-09-03", "Office hours are Wednesdays 3-4 PM in Room 412."),
        ],
        "syllabus": [("Midterm 1", "Oct 14, 11:00 AM"), ("Project 1", "Oct 23"), ("Final Exam", "Dec 18, finals")],
        "assignments": [
            ("Homework 1", "Due Sep 19 by 11:59 PM"),
            ("Homework 2", "Due Oct 3 by 11:59 PM"),
            ("Project 1", "Due Oct 23 by 11:59 PM"),
        ],
    },
    "linear-algebra": {
        "name": "MATH 240 Linear Algebra", "ou": "41002",
        "announcements": [("Textbook", "2026-09-02", "The 5th edition is fine; do not buy the 6th.")],
        "syllabus": [("Midterm", "Oct 21, in class"), ("Final Exam", "Dec 16, 8:00 AM")],
        "assignments": [
            ("Problem Set 1", "Due Sep 12 by 11:59 PM"),
            ("Problem Set 2", "Due Sep 26 by 11:59 PM"),
            ("Problem Set 3", "Due Oct 10 by 11:59 PM"),
            ("Problem Set 4", "Due Oct 24 by 11:59 PM"),
        ],
    },
    "physics-1": {
        "name": "PHYS 110 Physics I", "ou": "41003",
        "announcements": [("Lab safety", "2026-09-02", "Complete the safety module before your first lab.")],
        "syllabus": [("Exam 1", "Oct 7"), ("Exam 2", "Nov 11"), ("Final Exam", "Dec 17, 10:00 AM")],
        "assignments": [
            ("Lab Report 1", "Due Sep 25 by 5:00 PM"),
            ("Lab Report 2", "Due Oct 9 by 5:00 PM"),
            ("Lab Report 3", "Due Oct 30 by 5:00 PM"),
        ],
    },
    "writing-seminar": {
        "name": "WRIT 100 Writing Seminar", "ou": "41004",
        "announcements": [],
        "syllabus": [("Peer review workshop", "Oct 6")],
        "assignments": [
            ("Essay 1 draft", "Due Sep 29 by 11:59 PM"),
            ("Essay 1 final", "Due Oct 13 by 11:59 PM"),
            ("Essay 2 draft", "Due Nov 10 by 11:59 PM"),
        ],
    },
    "microeconomics": {
        "name": "ECON 150 Microeconomics", "ou": "41005",
        "announcements": [],
        "syllabus": [("Midterm", "Oct 20, 2026"), ("Final Exam", "Dec 15")],
        "assignments": [
            ("Problem Set 1", "Due Sep 18"),
            ("Problem Set 2", "Due Oct 9"),
            ("Problem Set 3", "Due Nov 13"),
        ],
    },
    "modern-history": {
        "name": "HIST 120 Modern History", "ou": "41006",
        "announcements": [("Museum visit", "2026-09-02", "The museum visit date is TBD; watch this space.")],
        "syllabus": [("Map quiz", "Sep 24"), ("Midterm essay", "Oct 22 to 24"), ("Final Exam", "Dec 19, 2:00 PM")],
        "assignments": [
            ("Reading response 1", "Due Sep 17 by 9:00 AM"),
            ("Reading response 2", "Due Oct 1 by 9:00 AM"),
            ("Research paper", "Due Dec 4 by 11:59 PM"),
        ],
    },
}

PLANTED = {
    "read_at": {"day0": "2026-09-05T23:00:00-04:00", "day1": "2026-09-06T23:00:00-04:00"},
    "changes": [
        {"type": "moved", "course_id": "data-structures", "title": "Midterm 1",
         "detail": "Oct 14, 11:00 AM -> Oct 16, 11:00 AM"},
        {"type": "added", "course_id": "linear-algebra", "title": "Problem Set 5",
         "detail": "Due Nov 6 by 11:59 PM"},
        {"type": "reworded", "course_id": "writing-seminar", "title": "Essay 1: first draft",
         "detail": "was 'Essay 1 draft', same due date"},
    ],
    "pending_removals": [
        {"course_id": "physics-1", "title": "Lab Report 2", "detail": "Due Oct 9 by 5:00 PM disappears"},
    ],
    "unreadable": [
        {"course_id": "microeconomics", "detail": "page replaced with an empty file"},
    ],
}


def _apply_day1(cid: str, spec: dict) -> dict:
    spec = json.loads(json.dumps(spec))
    if cid == "data-structures":
        spec["syllabus"] = [("Midterm 1", "Oct 16, 11:00 AM") if t == "Midterm 1" else (t, d) for t, d in spec["syllabus"]]
    elif cid == "linear-algebra":
        spec["assignments"].append(("Problem Set 5", "Due Nov 6 by 11:59 PM"))
    elif cid == "physics-1":
        spec["assignments"] = [(t, d) for t, d in spec["assignments"] if t != "Lab Report 2"]
    elif cid == "writing-seminar":
        spec["assignments"] = [("Essay 1: first draft", d) if t == "Essay 1 draft" else (t, d) for t, d in spec["assignments"]]
    return spec


def render(cid: str, spec: dict, day: str) -> str:
    noise = {
        "day0": {"sid": "8f3a19c2", "generated": "2026-09-05 23:00:12", "visited": "Sep 5, 2026 10:58 PM", "ago": "2 hours ago"},
        "day1": {"sid": "c71e04bb", "generated": "2026-09-06 23:00:41", "visited": "Sep 6, 2026 10:59 PM", "ago": "1 day ago"},
    }[day]
    ou = spec["ou"]
    ann = "\n".join(
        f'      <article class="announcement">\n'
        f'        <h3 class="title"><a href="/d2l/le/news/{ou}/{i + 1}/view?ou={ou}&sid={noise["sid"]}">{t}</a></h3>\n'
        f'        <time datetime="{d}">Posted {d}</time> <span class="meta">Posted {noise["ago"]}</span>\n'
        f'        <p>{body}</p>\n'
        f'      </article>'
        for i, (t, d, body) in enumerate(spec["announcements"])
    ) or "      <p class=\"empty\">No announcements.</p>"
    syl = "\n".join(
        f'        <tr><td>{t}</td><td class="date">{d}</td></tr>' for t, d in spec["syllabus"]
    )
    asg = "\n".join(
        f'        <li class="assignment">\n'
        f'          <a class="title" href="/d2l/lms/dropbox/user/folder_submit_files.d2l?db={100 + i}&ou={ou}&sid={noise["sid"]}">{t}</a>\n'
        f'          <span class="due">{d}</span>\n'
        f'        </li>'
        for i, (t, d) in enumerate(spec["assignments"])
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{spec["name"]} - Course Home</title>
</head>
<body class="d2l-body">
  <header class="d2l-header">
    <div class="d2l-timestamp">Last visited {noise["visited"]}</div>
  </header>
  <nav class="d2l-navigation">
    <a href="/d2l/home?sid={noise["sid"]}">My Home</a>
    <a href="/d2l/le/content/{ou}/Home?sid={noise["sid"]}">Content</a>
    <a href="/d2l/lms/dropbox/user/folders_list.d2l?ou={ou}&sid={noise["sid"]}">Assignments</a>
    <a href="/d2l/le/calendar/{ou}?sid={noise["sid"]}">Calendar</a>
  </nav>
  <main id="course-{ou}">
    <h1>{spec["name"]}</h1>

    <section id="announcements">
      <h2>Announcements</h2>
{ann}
    </section>

    <section id="syllabus">
      <h2>Syllabus schedule</h2>
      <table class="schedule">
        <tr><th>Item</th><th>Date</th></tr>
{syl}
      </table>
    </section>

    <section id="assignments">
      <h2>Assignments</h2>
      <ul class="assignments">
{asg}
      </ul>
    </section>
  </main>
  <footer class="d2l-footer">
    <span class="timestamp">Page generated {noise["generated"]}</span>
    <span class="session">Session {noise["sid"]}</span>
  </footer>
</body>
</html>
"""


def build(out_dir: Path = HERE) -> None:
    for day in ("day0", "day1"):
        d = out_dir / day
        d.mkdir(parents=True, exist_ok=True)
        for cid, spec in COURSES.items():
            if day == "day1" and cid == "microeconomics":
                (d / f"{cid}.html").write_text("", encoding="utf-8")
                continue
            s = spec if day == "day0" else _apply_day1(cid, spec)
            (d / f"{cid}.html").write_text(render(cid, s, day), encoding="utf-8")
    courses = [
        {"id": cid, "name": spec["name"], "platform": "brightspace",
         "url": f"{BASE_URL}/d2l/home/{spec['ou']}", "timezone": "America/New_York"}
        for cid, spec in COURSES.items()
    ]
    (out_dir / "courses.json").write_text(json.dumps(courses, indent=2) + "\n", encoding="utf-8")
    (out_dir / "expected.json").write_text(json.dumps(PLANTED, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
    print(f"fixtures written under {HERE}")
