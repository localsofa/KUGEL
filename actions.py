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