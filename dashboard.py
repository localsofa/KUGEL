from datetime import datetime
from rich.console import Console
from rich.text import Text

from database import get_connection


console = Console()


def get_open_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT task
        FROM todos
        WHERE completed = 0
        ORDER BY created_at DESC
        LIMIT 5
    """)

    tasks = cursor.fetchall()
    conn.close()

    return [task[0] for task in tasks]


def get_projects():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM projects
        ORDER BY created_at DESC
        LIMIT 5
    """)

    projects = cursor.fetchall()
    conn.close()

    return [project[0] for project in projects]


def get_recent_notes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content
        FROM notes
        ORDER BY created_at DESC
        LIMIT 5
    """)

    notes = cursor.fetchall()
    conn.close()

    return [note[0] for note in notes]


def show_overview(audio_mode=False):

    now = datetime.now()

    console.print()
    console.print(
        "════════════ KUGEL OVERVIEW ════════════",
        style="bold green"
    )

    console.print()

    # DATE
    console.print("DATE", style="bold green")
    console.print(now.strftime("%d.%m.%Y"))

    console.print()

    # TASKS
    console.print("OPEN TASKS", style="bold green")

    tasks = get_open_tasks()

    if tasks:
        for task in tasks:
            console.print(f"[ ] {task}")
    else:
        console.print("No open tasks.", style="dim")

    console.print()

    # PROJECTS
    console.print("PROJECTS", style="bold green")

    projects = get_projects()

    if projects:
        for project in projects:
            console.print(f"> {project}")
    else:
        console.print("No projects.", style="dim")

    console.print()

    # NOTES
    console.print("RECENT NOTES", style="bold green")

    notes = get_recent_notes()

    if notes:
        for note in notes:
            console.print(f"> {note}")
    else:
        console.print("No notes.", style="dim")

    console.print()

    # SYSTEM
    console.print("SYSTEM", style="bold green")

    console.print("● DATABASE ONLINE", style="green")
    console.print("● BRAIN ONLINE", style="green")

    if audio_mode:
        console.print("● AUDIO ONLINE", style="green")
    else:
        console.print("● AUDIO OFFLINE", style="dim")

    console.print()

    console.print(
        "════════════════════════════════════════",
        style="bold green"
    )

    console.print()


def show_tasks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task
        FROM todos
        WHERE completed = 0
        ORDER BY created_at DESC
    """)

    tasks = cursor.fetchall()
    conn.close()

    console.print()
    console.print(
        "════════════ KUGEL TASKS ════════════",
        style="bold green"
    )
    console.print()

    if not tasks:
        console.print("No open tasks.", style="dim")
    else:
        for task_id, task in tasks:
            console.print(f"[ ] {task_id}. {task}")

    console.print()
    console.print(
        "════════════════════════════════════",
        style="bold green"
    )
    console.print()


def show_projects():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, created_at
        FROM projects
        ORDER BY created_at DESC
    """)

    projects = cursor.fetchall()
    conn.close()

    console.print()
    console.print(
        "══════════ KUGEL PROJECTS ══════════",
        style="bold green"
    )
    console.print()

    if not projects:
        console.print("No projects.", style="dim")
    else:
        for project_id, name, created_at in projects:
            console.print(
                f"> {project_id}. {name}  "
                f"[dim]{created_at}[/dim]"
            )

    console.print()
    console.print(
        "════════════════════════════════════",
        style="bold green"
    )
    console.print()


def show_calendar():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, event_date, event_time
        FROM events
        ORDER BY event_date, event_time
        LIMIT 10
    """)

    events = cursor.fetchall()
    conn.close()

    console.print()
    console.print(
        "══════════ KUGEL CALENDAR ══════════",
        style="bold green"
    )
    console.print()

    if not events:
        console.print("No upcoming events.", style="dim")
    else:
        for event_id, title, event_date, event_time in events:

            if event_time:
                time_text = f" {event_time}"
            else:
                time_text = ""

            console.print(
                f"[{event_date}{time_text}] {title}"
            )

    console.print()
    console.print(
        "════════════════════════════════════",
        style="bold green"
    )
    console.print()