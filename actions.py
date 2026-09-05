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