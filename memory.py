import json

NOTES_FILE = "data/notes.json"
TODO_FILE = "data/todos.json"

# --- SAVE DATA ---
def save_note(text):

    try:
        with open(NOTES_FILE, "r") as f:
            notes = json.load(f)
    except:
        notes = []

    notes.append(text)

    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

def save_todo(text):
    try:
        with open(TODO_FILE, "r") as f:
            todos = json.load(f)
    except:
        todos = []

    todos.append(text)

    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)


# --- RETRIEVE DATA ---
def get_notes():
    try:
        with open(NOTES_FILE, "r") as f:
            notes = json.load(f)
        return "\n".join(notes[-10:])
    except:
        return "No notes yet."
    
def get_todos():
    try:
        with open(TODO_FILE, "r") as f:
            todos = json.load(f)
        return "\n".join(todos[-10:]) if todos else "No todos yet."
    except:
        return "No todos yet."