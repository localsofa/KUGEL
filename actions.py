from urllib.parse import urlsplit

from database import get_connection


def create_todo(task):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO todos (task) VALUES (?)",
        (task,)
    )

    conn.commit()
    conn.close()

    return f"Added '{task}' to your todo list."


def list_todos():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, task FROM todos WHERE completed = 0"
    )

    todos = cursor.fetchall()

    conn.close()

    if not todos:
        return "You don't have any open tasks."

    result = "Your tasks:\n"

    for todo_id, task in todos:
        result += f"{todo_id}. {task}\n"

    return result


def create_note(content):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO notes (content) VALUES (?)",
        (content,)
    )

    conn.commit()
    conn.close()

    return "I've saved that."


def create_project(name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO projects (name) VALUES (?)",
        (name,)
    )

    conn.commit()
    conn.close()

    return f"Project '{name}' created." 


def find_project(name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, name FROM projects WHERE name = ? COLLATE NOCASE LIMIT 1",
            (name.strip(),)
        )
        return cursor.fetchone()
    finally:
        conn.close()


def update_project(project_id, name, description, next_action):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE projects
            SET name = ?, description = ?, next_action = ?
            WHERE id = ?
            """,
            (name.strip(), description.strip(), next_action.strip(), project_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def save_project_note(project_id, content, note_id=None):
    content = content.strip()
    if not content:
        raise ValueError("A project note cannot be empty.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if note_id is None:
            cursor.execute(
                "INSERT INTO project_notes (project_id, content) VALUES (?, ?)",
                (project_id, content)
            )
        else:
            cursor.execute(
                """
                UPDATE project_notes
                SET content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND project_id = ?
                """,
                (content, note_id, project_id)
            )
            if not cursor.rowcount:
                raise ValueError("That project note no longer exists.")
        conn.commit()
    finally:
        conn.close()


def delete_project_note(project_id, note_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM project_notes WHERE id = ? AND project_id = ?",
            (note_id, project_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def save_project_link(project_id, title, url, link_id=None):
    title = title.strip()
    url = url.strip()
    parsed_url = urlsplit(url)
    if not title:
        raise ValueError("A link title cannot be empty.")
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        raise ValueError("Enter a complete http:// or https:// link.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if link_id is None:
            cursor.execute(
                """
                INSERT INTO project_links (project_id, title, url)
                VALUES (?, ?, ?)
                """,
                (project_id, title, url)
            )
        else:
            cursor.execute(
                """
                UPDATE project_links SET title = ?, url = ?
                WHERE id = ? AND project_id = ?
                """,
                (title, url, link_id, project_id)
            )
            if not cursor.rowcount:
                raise ValueError("That project link no longer exists.")
        conn.commit()
    finally:
        conn.close()


def delete_project_link(project_id, link_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM project_links WHERE id = ? AND project_id = ?",
            (link_id, project_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_project_todo(project_id, task):
    task = task.strip()
    if not task:
        raise ValueError("A project task cannot be empty.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO todos (task, project_id) VALUES (?, ?)",
            (task, project_id)
        )
        conn.commit()
    finally:
        conn.close()

    return f"Added '{task}' to the project."


def get_project_context(project_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT name, description, next_action FROM projects WHERE id = ?",
            (project_id,)
        )
        project = cursor.fetchone()
        if project is None:
            raise ValueError("That project no longer exists.")

        name, description, next_action = project
        cursor.execute(
            """
            SELECT content FROM project_notes
            WHERE project_id = ? ORDER BY updated_at DESC LIMIT 30
            """,
            (project_id,)
        )
        notes = [row[0] for row in cursor.fetchall()]
        cursor.execute(
            """
            SELECT title, url FROM project_links
            WHERE project_id = ? ORDER BY created_at DESC LIMIT 30
            """,
            (project_id,)
        )
        links = cursor.fetchall()
        cursor.execute(
            """
            SELECT task FROM todos
            WHERE project_id = ? AND completed = 0
            ORDER BY created_at DESC LIMIT 30
            """,
            (project_id,)
        )
        tasks = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    return (
        f"Project: {name}\n"
        f"Description: {description or '(none)'}\n"
        f"Next action: {next_action or '(none)'}\n"
        "Notes:\n" + ("\n".join(f"- {note}" for note in notes) or "- (none)") + "\n"
        "Links:\n" + (
            "\n".join(f"- {title}: {url}" for title, url in links) or "- (none)"
        ) + "\n"
        "Open tasks:\n" + ("\n".join(f"- {task}" for task in tasks) or "- (none)")
    )


def create_event(title, event_date, event_time=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO events (title, event_date, event_time)
        VALUES (?, ?, ?)
        """,
        (title, event_date, event_time)
    )

    conn.commit()
    conn.close()

    if event_time:
        return f"Event '{title}' added for {event_date} at {event_time}."
    else:
        return f"Event '{title}' added for {event_date}."


def list_events():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, event_date, event_time
        FROM events
        ORDER BY event_date, event_time
    """)

    events = cursor.fetchall()
    conn.close()

    if not events:
        return "You don't have any upcoming events."

    result = "Your upcoming events:\n"

    for event_id, title, event_date, event_time in events:
        if event_time:
            result += f"{event_id}. {event_date} {event_time} - {title}\n"
        else:
            result += f"{event_id}. {event_date} - {title}\n"

    return result


def complete_todo(todo_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE todos SET completed = 1 WHERE id = ?",
        (todo_id,)
    )

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    if updated:
        return True

    return False