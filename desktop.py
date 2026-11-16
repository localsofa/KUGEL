import tkinter as tk
import calendar as pycalendar
import tkinter.font as tkfont
import webbrowser
from urllib.parse import urlsplit

from tkinter import simpledialog, messagebox
from datetime import datetime, date

from brain import process
from database import get_connection, init_database
from actions import (
    complete_todo,
    create_project,
    create_project_todo,
    delete_project_link,
    delete_project_note,
    find_project,
    save_project_link,
    save_project_note,
    update_project,
)
from llm import assist_with_project


# ==========================================
# KUGEL CONFIGURATION
# ==========================================

BG = "#080d0a"
PANEL = "#101a13"
PANEL_LIGHT = "#17251a"
GREEN = "#62ff8b"
GREEN_DIM = "#329b50"
TEXT = "#d7e8d9"
MUTED = "#789580"

FONT = ("Consolas", 10)
FONT_BOLD = ("Consolas", 11, "bold")

init_database()


# ==========================================
# DATABASE HELPERS
# ==========================================

def fetch_rows(query, parameters=()):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, parameters)
        return cursor.fetchall()
    finally:
        conn.close()


def get_tasks():
    return fetch_rows("""
        SELECT id, task
        FROM todos
        WHERE completed = 0
        ORDER BY created_at DESC
        LIMIT 8
    """)


def get_projects():
    return fetch_rows("""
        SELECT id, name, next_action
        FROM projects
        ORDER BY created_at DESC
    """)


def get_project_notes(project_id):
    return fetch_rows("""
        SELECT id, content
        FROM project_notes
        WHERE project_id = ?
        ORDER BY updated_at DESC
    """, (project_id,))


def get_project_links(project_id):
    return fetch_rows("""
        SELECT id, title, url
        FROM project_links
        WHERE project_id = ?
        ORDER BY created_at DESC
    """, (project_id,))


def get_project_tasks(project_id):
    return fetch_rows("""
        SELECT id, task, completed
        FROM todos
        WHERE project_id = ?
        ORDER BY completed, created_at DESC
    """, (project_id,))


def get_events():
    try:
        return fetch_rows("""
            SELECT title, event_date, event_time
            FROM events
            WHERE event_date >= date('now', 'localtime')
            ORDER BY event_date, event_time
            LIMIT 8
        """)
    except Exception:
        # The events table may not exist in an older database.
        return []


def get_notes():
    return fetch_rows("""
        SELECT content
        FROM notes
        ORDER BY created_at DESC
        LIMIT 5
    """)


# ==========================================
# DESKTOP APPLICATION
# ==========================================

class KugelDesktop:

    def __init__(self, root):
        self.root = root

        self.root.title("KUGEL // Personal Assistant")
        self.root.geometry("1100x720")
        self.root.minsize(850, 580)
        self.root.configure(bg=BG)

        self.current_view = "OVERVIEW"
        self.active_project_id = None

        self.calendar_year = date.today().year
        self.calendar_month = date.today().month
        self.selected_date = date.today()

        self.build_header()
        self.build_layout()
        self.show_overview()

        self.add_message(
            "KUGEL",
            "Systems online. I'm ready. What shall we work on?"
        )

        self.root.after(1000, self.update_clock)

    # --------------------------------------
    # HEADER
    # --------------------------------------

    def build_header(self):
        header = tk.Frame(
            self.root,
            bg=BG,
            padx=22,
            pady=15
        )
        header.pack(fill="x")

        tk.Label(
            header,
            text="◉ KUGEL",
            font=("Consolas", 19, "bold"),
            fg=GREEN,
            bg=BG
        ).pack(side="left")

        tk.Label(
            header,
            text="PERSONAL SYSTEM  //  LOCAL INTERFACE",
            font=("Consolas", 9),
            fg=MUTED,
            bg=BG
        ).pack(side="left", padx=18, pady=7)

        self.clock = tk.Label(
            header,
            text="",
            font=FONT,
            fg=GREEN,
            bg=BG
        )
        self.clock.pack(side="right")

        tk.Frame(
            self.root,
            bg=GREEN_DIM,
            height=1
        ).pack(fill="x", padx=22)

    # --------------------------------------
    # MAIN LAYOUT
    # --------------------------------------

    def build_layout(self):
        layout = tk.Frame(self.root, bg=BG, padx=22, pady=18)
        layout.pack(fill="both", expand=True)

        # Left navigation
        self.sidebar = tk.Frame(
            layout,
            bg=PANEL,
            width=175,
            padx=12,
            pady=15
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 14))
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="NAVIGATION",
            font=FONT_BOLD,
            fg=GREEN,
            bg=PANEL
        ).pack(anchor="w", pady=(0, 15))

        buttons = [
            ("OVERVIEW", self.show_overview),
            ("TASKS", self.show_tasks),
            ("PROJECTS", self.show_projects),
            ("CALENDAR", self.show_calendar),
            ("NOTES", self.show_notes),
        ]

        for label, command in buttons:
            tk.Button(
                self.sidebar,
                text=f"> {label}",
                command=command,
                anchor="w",
                font=FONT,
                fg=TEXT,
                bg=PANEL,
                activeforeground=GREEN,
                activebackground=PANEL_LIGHT,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=8,
                pady=9
            ).pack(fill="x", pady=2)

        tk.Frame(
            self.sidebar,
            bg=GREEN_DIM,
            height=1
        ).pack(fill="x", pady=18)

        tk.Label(
            self.sidebar,
            text="SYSTEM STATUS",
            font=FONT_BOLD,
            fg=GREEN,
            bg=PANEL
        ).pack(anchor="w", pady=(0, 10))

        for label in ("DATABASE", "BRAIN", "INTERFACE"):
            tk.Label(
                self.sidebar,
                text=f"● {label} ONLINE",
                font=("Consolas", 8),
                fg=GREEN_DIM,
                bg=PANEL
            ).pack(anchor="w", pady=3)

        # Right side: content and chat
        right = tk.Frame(layout, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self.view_title = tk.Label(
            right,
            text="OVERVIEW",
            font=("Consolas", 15, "bold"),
            fg=GREEN,
            bg=BG
        )
        self.view_title.pack(anchor="w", pady=(0, 12))

        self.content = tk.Frame(right, bg=BG)
        self.content.pack(fill="both", expand=True)

        # Chat panel
        chat = tk.Frame(
            right,
            bg=PANEL,
            padx=12,
            pady=10
        )
        chat.pack(fill="x", pady=(14, 0))

        tk.Label(
            chat,
            text="KUGEL TERMINAL",
            font=FONT_BOLD,
            fg=GREEN,
            bg=PANEL
        ).pack(anchor="w", pady=(0, 8))

        self.chat_history = tk.Text(
            chat,
            height=7,
            bg=BG,
            fg=TEXT,
            insertbackground=GREEN,
            font=FONT,
            relief="flat",
            wrap="word",
            padx=8,
            pady=8,
            state="disabled"
        )
        self.chat_history.pack(fill="x", pady=(0, 8))

        self.chat_history.tag_configure(
            "speaker",
            foreground=GREEN
        )
        self.chat_history.tag_configure(
            "user",
            foreground="#8bbcff"
        )

        input_row = tk.Frame(chat, bg=PANEL)
        input_row.pack(fill="x")

        self.input = tk.Entry(
            input_row,
            bg=PANEL_LIGHT,
            fg=TEXT,
            insertbackground=GREEN,
            font=FONT,
            relief="flat"
        )
        self.input.pack(side="left", fill="x", expand=True, ipady=9)
        self.input.bind("<Return>", self.send_message)

        tk.Button(
            input_row,
            text="SEND",
            command=self.send_message,
            font=FONT_BOLD,
            fg=BG,
            bg=GREEN,
            activebackground="#a0ffb5",
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2"
        ).pack(side="left", padx=(8, 0))

        self.input.focus_set()

    # --------------------------------------
    # CONTENT HELPERS
    # --------------------------------------

    def clear_content(self, title):
        self.current_view = title

        self.view_title.config(text=title)

        for widget in self.content.winfo_children():
            widget.destroy()

    def add_section(self, title, parent=None):
        tk.Label(
            parent or self.content,
            text=title,
            font=FONT_BOLD,
            fg=GREEN,
            bg=BG
        ).pack(anchor="w", pady=(12, 5))

    def add_line(self, text, color=TEXT, parent=None):
        tk.Label(
            parent or self.content,
            text=text,
            font=FONT,
            fg=color,
            bg=BG,
            anchor="w",
            justify="left",
            wraplength=650
        ).pack(anchor="w", fill="x", pady=2)

    def add_message(self, speaker, message):
        self.chat_history.config(state="normal")

        tag = "user" if speaker == "YOU" else "speaker"

        self.chat_history.insert(
            "end",
            f"{speaker} > ",
            tag
        )
        self.chat_history.insert("end", f"{message}\n\n")

        self.chat_history.see("end")
        self.chat_history.config(state="disabled")

    # --------------------------------------
    # OVERVIEW
    # --------------------------------------

    def show_overview(self):
        self.active_project_id = None
        self.clear_content("KUGEL OVERVIEW")

        self.add_section("TODAY")
        self.add_line(datetime.now().strftime("%A, %d.%m.%Y"))

        self.add_section("OPEN TASKS")
        tasks = get_tasks()

        if tasks:
            for task_id, task in tasks:
                self.add_line(f"[ ] {task_id}. {task}")
        else:
            self.add_line("No open tasks.", MUTED)

        self.add_section("PROJECTS")
        projects = get_projects()

        if projects:
            for _, name, _ in projects:
                self.add_line(f"> {name}")
        else:
            self.add_line("No projects yet.", MUTED)

        self.add_section("UPCOMING EVENTS")
        events = get_events()

        if events:
            for title, event_date, event_time in events:
                time_text = f" {event_time}" if event_time else ""
                self.add_line(f"> {event_date}{time_text}  {title}")
        else:
            self.add_line("No upcoming events.", MUTED)

        tk.Button(
            self.content,
            text="REFRESH OVERVIEW",
            command=self.show_overview,
            font=FONT,
            fg=GREEN,
            bg=PANEL,
            activebackground=PANEL_LIGHT,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7
        ).pack(anchor="w", pady=15)

    # --------------------------------------
    # TASKS
    # --------------------------------------

    def show_tasks(self):
        self.active_project_id = None
        self.clear_content("TASKS")

        self.add_section("YOUR OPEN TASKS")

        tasks = get_tasks()

        if not tasks:
            self.add_line("All clear. No open tasks.", MUTED)
        else:
            for task_id, task in tasks:
                row = tk.Frame(self.content, bg=BG)
                row.pack(fill="x", pady=4)

                completed_font = tkfont.Font(
                    family="Consolas",
                    size=10,
                    overstrike=True
                )

                task_label = tk.Label(
                    row,
                    text=task,
                    font=FONT,
                    fg=TEXT,
                    bg=BG,
                    anchor="w"
                )
                task_label.pack(side="left", fill="x", expand=True)

                checkbox = tk.Checkbutton(
                    row,
                    text="",
                    bg=BG,
                    fg=GREEN,
                    activebackground=BG,
                    activeforeground=GREEN,
                    selectcolor=PANEL,
                    cursor="hand2",
                    command=lambda tid=task_id,
                                   label=task_label,
                                   cb_font=completed_font:
                        self.finish_task(tid, label, cb_font)
                )
                checkbox.pack(side="left", before=task_label)

        self.add_section("QUICK TIP")
        self.add_line(
            "Click a checkbox to complete a task.",
            MUTED
        )
        self.add_line(
            'You can also type: Add todo water the plants',
            MUTED
        )

    def finish_task(self, task_id, label, completed_font):
        # Save completion in the database immediately.
        if not complete_todo(task_id):
            messagebox.showerror(
                "KUGEL",
                "I couldn't update that task."
            )
            return

        # Show the crossed-out state briefly.
        label.config(
            font=completed_font,
            fg=GREEN_DIM
        )

        # Then remove it from the open task list.
        self.root.after(1000, self.show_tasks)

    # --------------------------------------
    # PROJECTS
    # --------------------------------------

    def show_projects(self):
        self.active_project_id = None
        self.clear_content("PROJECTS")

        header = tk.Frame(self.content, bg=BG)
        header.pack(fill="x")
        self.add_section("YOUR PROJECTS", parent=header)
        tk.Button(
            header,
            text="+ NEW PROJECT",
            command=self.create_project_from_page,
            font=FONT_BOLD,
            fg=BG,
            bg=GREEN,
            activebackground="#a0ffb5",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6
        ).pack(side="right", pady=(8, 0))

        projects = get_projects()

        if projects:
            for project_id, name, next_action in projects:
                row = tk.Frame(self.content, bg=PANEL, padx=10, pady=8)
                row.pack(fill="x", pady=4)
                tk.Button(
                    row,
                    text=f"> {name}",
                    command=lambda pid=project_id: self.open_project(pid),
                    font=FONT_BOLD,
                    fg=GREEN,
                    bg=PANEL,
                    activebackground=PANEL_LIGHT,
                    relief="flat",
                    cursor="hand2",
                    anchor="w"
                ).pack(fill="x")
                if next_action:
                    self.add_line(
                        f"Next: {next_action}",
                        MUTED,
                        parent=row
                    )
        else:
            self.add_line("No projects created yet.", MUTED)

        self.add_line("")
        self.add_line(
            "Open a project to keep its overview, ideas, links, and tasks together.",
            MUTED
        )

    def create_project_from_page(self):
        name = simpledialog.askstring(
            "KUGEL // New project",
            "Project name:",
            parent=self.root
        )
        if not name or not name.strip():
            return

        try:
            if find_project(name):
                messagebox.showerror(
                    "KUGEL // Projects",
                    "A project with that name already exists.",
                    parent=self.root
                )
                return
            create_project(name.strip())
            project = find_project(name.strip())
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Projects",
                f"Couldn't create the project:\n{error}",
                parent=self.root
            )
            return

        if project is None:
            messagebox.showerror(
                "KUGEL // Projects",
                "The project was created but couldn't be loaded.",
                parent=self.root
            )
            return
        self.open_project(project[0])

    def open_project(self, project_id):
        rows = fetch_rows(
            """
            SELECT name, description, next_action
            FROM projects WHERE id = ?
            """,
            (project_id,)
        )
        if not rows:
            messagebox.showerror(
                "KUGEL // Projects",
                "That project no longer exists.",
                parent=self.root
            )
            self.show_projects()
            return

        name, description, next_action = rows[0]
        self.active_project_id = project_id
        self.clear_content(name.upper())
        self.current_view = "PROJECT_DETAIL"

        scroll_area = tk.Frame(self.content, bg=BG)
        scroll_area.pack(fill="both", expand=True)
        canvas = tk.Canvas(
            scroll_area,
            bg=BG,
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            scroll_area,
            orient="vertical",
            command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        workspace = tk.Frame(canvas, bg=BG)
        window_id = canvas.create_window(
            (0, 0),
            window=workspace,
            anchor="nw"
        )
        workspace.bind(
            "<Configure>",
            lambda event: event.widget.configure(
                scrollregion=event.widget.bbox("all")
            )
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width)
        )

        tk.Button(
            workspace,
            text="< ALL PROJECTS",
            command=self.show_projects,
            font=FONT,
            fg=GREEN,
            bg=PANEL,
            activebackground=PANEL_LIGHT,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            workspace,
            text=name,
            font=("Consolas", 17, "bold"),
            fg=GREEN,
            bg=BG,
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        controls = tk.Frame(workspace, bg=BG)
        controls.pack(fill="x")
        buttons = [
            ("EDIT DETAILS", self.edit_project),
            ("+ NOTE", lambda: self.edit_project_note(project_id)),
            ("+ LINK", lambda: self.edit_project_link(project_id)),
            ("+ TASK", lambda: self.add_project_task(project_id)),
            ("KUGEL SUMMARY", lambda: self.run_project_assistance(project_id, "summary")),
            ("NEXT STEPS", lambda: self.run_project_assistance(project_id, "next_steps")),
        ]
        for label, command in buttons:
            tk.Button(
                controls,
                text=label,
                command=command,
                font=FONT,
                fg=GREEN,
                bg=PANEL,
                activebackground=PANEL_LIGHT,
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=5
            ).pack(side="left", padx=(0, 5), pady=(0, 8))

        self.add_section("OVERVIEW", parent=workspace)
        self.add_line(
            description or "Add a description to capture the project goal.",
            MUTED if not description else TEXT,
            parent=workspace
        )
        self.add_section("NEXT ACTION", parent=workspace)
        self.add_line(
            next_action or "Set the next small step for this project.",
            MUTED if not next_action else TEXT,
            parent=workspace
        )

        self.add_section("BRAINSTORM NOTES", parent=workspace)
        notes = get_project_notes(project_id)
        if notes:
            for note_id, content in notes:
                row = tk.Frame(workspace, bg=PANEL, padx=8, pady=6)
                row.pack(fill="x", pady=3)
                tk.Label(
                    row,
                    text=content,
                    font=FONT,
                    fg=TEXT,
                    bg=PANEL,
                    anchor="w",
                    justify="left",
                    wraplength=600
                ).pack(side="left", fill="x", expand=True)
                tk.Button(
                    row,
                    text="EDIT",
                    command=lambda nid=note_id, value=content:
                        self.edit_project_note(project_id, nid, value),
                    font=FONT,
                    fg=GREEN,
                    bg=PANEL_LIGHT,
                    relief="flat",
                    cursor="hand2"
                ).pack(side="right", padx=(8, 0))
                tk.Button(
                    row,
                    text="X",
                    command=lambda nid=note_id:
                        self.remove_project_note(project_id, nid),
                    font=FONT,
                    fg=TEXT,
                    bg=PANEL_LIGHT,
                    relief="flat",
                    cursor="hand2"
                ).pack(side="right")
        else:
            self.add_line("No ideas captured yet.", MUTED, parent=workspace)

        self.add_section("USEFUL LINKS", parent=workspace)
        links = get_project_links(project_id)
        if links:
            for link_id, title, url in links:
                row = tk.Frame(workspace, bg=PANEL, padx=8, pady=6)
                row.pack(fill="x", pady=3)
                tk.Button(
                    row,
                    text=title,
                    command=lambda target=url: self.open_project_link(target),
                    font=FONT,
                    fg=GREEN,
                    bg=PANEL,
                    activebackground=PANEL_LIGHT,
                    relief="flat",
                    cursor="hand2",
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)
                tk.Button(
                    row,
                    text="EDIT",
                    command=lambda lid=link_id, label=title, target=url:
                        self.edit_project_link(project_id, lid, label, target),
                    font=FONT,
                    fg=GREEN,
                    bg=PANEL_LIGHT,
                    relief="flat",
                    cursor="hand2"
                ).pack(side="right", padx=(8, 0))
                tk.Button(
                    row,
                    text="X",
                    command=lambda lid=link_id:
                        self.remove_project_link(project_id, lid),
                    font=FONT,
                    fg=TEXT,
                    bg=PANEL_LIGHT,
                    relief="flat",
                    cursor="hand2"
                ).pack(side="right")
        else:
            self.add_line("No links saved yet.", MUTED, parent=workspace)

        self.add_section("PROJECT TASKS", parent=workspace)
        tasks = get_project_tasks(project_id)
        if tasks:
            for task_id, task, completed in tasks:
                variable = tk.IntVar(value=completed)
                tk.Checkbutton(
                    workspace,
                    text=task,
                    variable=variable,
                    state="disabled" if completed else "normal",
                    command=lambda tid=task_id:
                        self.complete_project_task(project_id, tid),
                    bg=BG,
                    fg=MUTED if completed else TEXT,
                    activebackground=BG,
                    activeforeground=GREEN,
                    selectcolor=PANEL,
                    font=FONT,
                    anchor="w",
                    justify="left",
                    wraplength=650
                ).pack(fill="x", pady=2)
        else:
            self.add_line("No tasks linked to this project yet.", MUTED, parent=workspace)

        self.add_section("KUGEL WORKFLOW", parent=workspace)
        self.add_line(
            'In chat: "Remember [idea]" or "Add todo [task]" saves to this project while it is open.',
            MUTED,
            parent=workspace
        )
        self.add_line(
            'Named capture: "Add idea to project NAME: ...", "Add link to project NAME: Title | URL", '
            'or "Add task to project NAME: ...".',
            MUTED,
            parent=workspace
        )
        self.add_line(
            'Ask for help: "Summarize project NAME" or "Suggest next steps for project NAME".',
            MUTED,
            parent=workspace
        )

    def ask_multiline(self, title, prompt, initial=""):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.geometry("520x320")
        dialog.configure(bg=BG)

        tk.Label(
            dialog,
            text=prompt,
            font=FONT_BOLD,
            fg=GREEN,
            bg=BG
        ).pack(anchor="w", padx=12, pady=(12, 6))
        editor = tk.Text(
            dialog,
            bg=PANEL,
            fg=TEXT,
            insertbackground=GREEN,
            font=FONT,
            wrap="word",
            relief="flat"
        )
        editor.pack(fill="both", expand=True, padx=12, pady=6)
        editor.insert("1.0", initial)

        result = []

        def finish(save):
            if save:
                result.append(editor.get("1.0", "end-1c").strip())
            dialog.destroy()

        buttons = tk.Frame(dialog, bg=BG)
        buttons.pack(fill="x", padx=12, pady=(4, 12))
        tk.Button(
            buttons,
            text="CANCEL",
            command=lambda: finish(False),
            font=FONT,
            fg=TEXT,
            bg=PANEL,
            relief="flat"
        ).pack(side="right", padx=(6, 0))
        tk.Button(
            buttons,
            text="SAVE",
            command=lambda: finish(True),
            font=FONT_BOLD,
            fg=BG,
            bg=GREEN,
            relief="flat"
        ).pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.grab_set()
        editor.focus_set()
        self.root.wait_window(dialog)
        return result[0] if result else None

    def edit_project(self):
        project_id = self.active_project_id
        if project_id is None:
            return
        name, description, next_action = fetch_rows(
            "SELECT name, description, next_action FROM projects WHERE id = ?",
            (project_id,)
        )[0]
        new_name = simpledialog.askstring(
            "KUGEL // Edit project",
            "Project name:",
            initialvalue=name,
            parent=self.root
        )
        if new_name is None or not new_name.strip():
            return
        existing_project = find_project(new_name)
        if existing_project is not None and existing_project[0] != project_id:
            messagebox.showerror(
                "KUGEL // Projects",
                "A project with that name already exists.",
                parent=self.root
            )
            return
        new_description = self.ask_multiline(
            "KUGEL // Project overview",
            "Project goal and context:",
            description or ""
        )
        if new_description is None:
            return
        new_next_action = simpledialog.askstring(
            "KUGEL // Next action",
            "What's the next small step?",
            initialvalue=next_action or "",
            parent=self.root
        )
        if new_next_action is None:
            return
        try:
            if not update_project(
                project_id,
                new_name,
                new_description,
                new_next_action
            ):
                raise ValueError("The project could not be updated.")
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Projects",
                f"Couldn't update the project:\n{error}",
                parent=self.root
            )
            return
        self.open_project(project_id)

    def edit_project_note(self, project_id, note_id=None, initial=""):
        content = self.ask_multiline(
            "KUGEL // Project note",
            "Idea or note:",
            initial
        )
        if content is None:
            return
        try:
            save_project_note(project_id, content, note_id)
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Project note",
                f"Couldn't save the note:\n{error}",
                parent=self.root
            )
            return
        self.open_project(project_id)

    def remove_project_note(self, project_id, note_id):
        if not messagebox.askyesno(
            "KUGEL // Project note",
            "Delete this note?",
            parent=self.root
        ):
            return
        try:
            if not delete_project_note(project_id, note_id):
                raise ValueError("That note no longer exists.")
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Project note",
                f"Couldn't delete the note:\n{error}",
                parent=self.root
            )
            return
        self.open_project(project_id)

    def edit_project_link(self, project_id, link_id=None, title="", url=""):
        new_title = simpledialog.askstring(
            "KUGEL // Project link",
            "Link title:",
            initialvalue=title,
            parent=self.root
        )
        if new_title is None:
            return
        new_url = simpledialog.askstring(
            "KUGEL // Project link",
            "URL (http:// or https://):",
            initialvalue=url,
            parent=self.root
        )
        if new_url is None:
            return
        try:
            save_project_link(project_id, new_title, new_url, link_id)
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Project link",
                f"Couldn't save the link:\n{error}",
                parent=self.root
            )
            return
        self.open_project(project_id)

    def remove_project_link(self, project_id, link_id):
        if not messagebox.askyesno(
            "KUGEL // Project link",
            "Remove this link?",
            parent=self.root
        ):
            return
        try:
            if not delete_project_link(project_id, link_id):
                raise ValueError("That link no longer exists.")
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Project link",
                f"Couldn't remove the link:\n{error}",
                parent=self.root
            )
            return
        self.open_project(project_id)

    def open_project_link(self, url):
        parsed_url = urlsplit(url)
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            messagebox.showerror(
                "KUGEL // Project link",
                "This link isn't a valid web URL.",
                parent=self.root
            )
            return
        try:
            if not webbrowser.open(url):
                raise RuntimeError("No browser accepted the link.")
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Project link",
                f"Couldn't open the link:\n{error}",
                parent=self.root
            )

    def add_project_task(self, project_id):
        task = simpledialog.askstring(
            "KUGEL // Project task",
            "Task:",
            parent=self.root
        )
        if task is None:
            return
        try:
            create_project_todo(project_id, task)
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Project task",
                f"Couldn't save the task:\n{error}",
                parent=self.root
            )
            return
        self.open_project(project_id)

    def complete_project_task(self, project_id, task_id):
        if not complete_todo(task_id):
            messagebox.showerror(
                "KUGEL // Project task",
                "Couldn't complete that task.",
                parent=self.root
            )
            return
        self.open_project(project_id)

    def run_project_assistance(self, project_id, mode):
        try:
            result = assist_with_project(project_id, mode)
        except Exception as error:
            messagebox.showerror(
                "KUGEL // Project assistant",
                f"KUGEL couldn't help with this project:\n{error}\n\n"
                "Make sure Ollama is running locally with the configured model.",
                parent=self.root
            )
            return
        self.add_message("KUGEL", result)

    # --------------------------------------
    # CALENDAR
    # --------------------------------------

    def show_calendar(self):
        self.active_project_id = None
        self.clear_content("CALENDAR")

        # Header and month navigation
        header = tk.Frame(self.content, bg=BG)
        header.pack(fill="x", pady=(0, 12))

        tk.Button(
            header,
            text="<",
            command=self.previous_month,
            font=FONT_BOLD,
            fg=GREEN,
            bg=PANEL,
            relief="flat",
            cursor="hand2",
            width=3
        ).pack(side="left")

        self.month_label = tk.Label(
            header,
            text="",
            font=("Consolas", 14, "bold"),
            fg=GREEN,
            bg=BG
        )
        self.month_label.pack(side="left", expand=True)

        tk.Button(
            header,
            text=">",
            command=self.next_month,
            font=FONT_BOLD,
            fg=GREEN,
            bg=PANEL,
            relief="flat",
            cursor="hand2",
            width=3
        ).pack(side="right")

        tk.Button(
            self.content,
            text="TODAY",
            command=self.go_to_today,
            font=FONT,
            fg=GREEN,
            bg=PANEL,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4
        ).pack(anchor="e", pady=(0, 8))

        # Calendar grid
        self.calendar_grid = tk.Frame(self.content, bg=BG)
        self.calendar_grid.pack(fill="x")

        # Events for the selected date
        self.add_section("SELECTED DAY")

        self.selected_day_label = tk.Label(
            self.content,
            text="",
            font=FONT_BOLD,
            fg=GREEN,
            bg=BG
        )
        self.selected_day_label.pack(anchor="w", pady=(0, 5))

        self.day_events_frame = tk.Frame(self.content, bg=BG)
        self.day_events_frame.pack(fill="x")

        tk.Button(
            self.content,
            text="+ ADD EVENT",
            command=self.add_calendar_event,
            font=FONT_BOLD,
            fg=BG,
            bg=GREEN,
            activebackground="#a0ffb5",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7
        ).pack(anchor="w", pady=12)

        self.render_calendar()

    def render_calendar(self):
        # Remove the previous month's grid.
        for widget in self.calendar_grid.winfo_children():
            widget.destroy()

        month_name = date(
            self.calendar_year,
            self.calendar_month,
            1
        ).strftime("%B %Y")

        self.month_label.config(text=month_name)

        # Get event dates for the visible month.
        try:
            rows = fetch_rows("""
                SELECT event_date
                FROM events
            """)
            event_dates = {row[0] for row in rows}
        except Exception:
            event_dates = set()

        # Weekday headings, Monday through Sunday.
        weekdays = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

        for col, weekday in enumerate(weekdays):
            tk.Label(
                self.calendar_grid,
                text=weekday,
                font=("Consolas", 9, "bold"),
                fg=MUTED,
                bg=BG,
                width=4
            ).grid(row=0, column=col, padx=2, pady=4)

        month = pycalendar.monthcalendar(
            self.calendar_year,
            self.calendar_month
        )

        today = date.today()

        for row_index, week in enumerate(month, start=1):
            for col_index, day in enumerate(week):
                if day == 0:
                    tk.Label(
                        self.calendar_grid,
                        text="",
                        bg=BG,
                        width=4
                    ).grid(
                        row=row_index,
                        column=col_index,
                        padx=2,
                        pady=2
                    )
                    continue

                current_date = date(
                    self.calendar_year,
                    self.calendar_month,
                    day
                )

                date_string = current_date.isoformat()
                has_events = date_string in event_dates
                is_selected = current_date == self.selected_date
                is_today = current_date == today

                if is_selected:
                    bg = GREEN
                    fg = BG
                elif is_today:
                    bg = PANEL_LIGHT
                    fg = GREEN
                else:
                    bg = PANEL
                    fg = TEXT

                # The small dot marks days with events.
                marker = " •" if has_events else ""

                button = tk.Button(
                    self.calendar_grid,
                    text=f"{day}{marker}",
                    command=lambda d=current_date: self.select_calendar_day(d),
                    font=("Consolas", 9, "bold" if is_selected else "normal"),
                    fg=fg,
                    bg=bg,
                    activeforeground=BG,
                    activebackground=GREEN,
                    relief="flat",
                    cursor="hand2",
                    width=4,
                    padx=0,
                    pady=6
                )
                button.grid(
                    row=row_index,
                    column=col_index,
                    padx=2,
                    pady=2,
                    sticky="nsew"
                )

        for col in range(7):
            self.calendar_grid.grid_columnconfigure(
                col,
                weight=1
            )

        self.render_selected_day()

    def select_calendar_day(self, selected_date):
        self.selected_date = selected_date
        self.render_calendar()

    def render_selected_day(self):
        self.selected_day_label.config(
            text=self.selected_date.strftime("%A, %d %B %Y")
        )

        for widget in self.day_events_frame.winfo_children():
            widget.destroy()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT title, event_time
                FROM events
                WHERE event_date = ?
                ORDER BY event_time
            """, (self.selected_date.isoformat(),))

            events = cursor.fetchall()
            conn.close()

        except Exception:
            events = []

        if not events:
            tk.Label(
                self.day_events_frame,
                text="Nothing scheduled for this day.",
                font=FONT,
                fg=MUTED,
                bg=BG
            ).pack(anchor="w", pady=4)
            return

        for title, event_time in events:
            time_text = event_time if event_time else "ALL DAY"

            tk.Label(
                self.day_events_frame,
                text=f"●  {time_text}   {title}",
                font=FONT,
                fg=TEXT,
                bg=BG,
                anchor="w",
                wraplength=600
            ).pack(anchor="w", fill="x", pady=3)

    def previous_month(self):
        if self.calendar_month == 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        else:
            self.calendar_month -= 1

        self.render_calendar()

    def next_month(self):
        if self.calendar_month == 12:
            self.calendar_month = 1
            self.calendar_year += 1
        else:
            self.calendar_month += 1

        self.render_calendar()

    def go_to_today(self):
        today = date.today()

        self.calendar_year = today.year
        self.calendar_month = today.month
        self.selected_date = today

        self.render_calendar()

    def add_calendar_event(self):
        title = simpledialog.askstring(
            "KUGEL // New Event",
            "What is the event?",
            parent=self.root
        )

        if not title or not title.strip():
            return

        time_text = simpledialog.askstring(
            "KUGEL // New Event",
            "Time (HH:MM), or leave blank for all-day:",
            parent=self.root
        )

        time_text = (time_text or "").strip() or None

        # Validate the optional time.
        if time_text:
            try:
                datetime.strptime(time_text, "%H:%M")
            except ValueError:
                messagebox.showerror(
                    "Invalid time",
                    "Please enter a time like 14:30, or leave it blank."
                )
                return

        # Store the selected date and event in SQLite.
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO events (title, event_date, event_time)
                VALUES (?, ?, ?)
            """, (
                title.strip(),
                self.selected_date.isoformat(),
                time_text
            ))

            conn.commit()
            conn.close()

        except Exception as error:
            messagebox.showerror(
                "KUGEL // Database error",
                f"Couldn't save the event:\n{error}"
            )
            return

        self.render_calendar()
        self.add_message(
            "KUGEL",
            f"Event saved: {title.strip()} on {self.selected_date.isoformat()}."
        )

    # --------------------------------------
    # NOTES
    # --------------------------------------

    def show_notes(self):
        self.active_project_id = None
        self.clear_content("NOTES")

        self.add_section("RECENT NOTES")
        notes = get_notes()

        if notes:
            for (content,) in notes:
                self.add_line(f"> {content}")
        else:
            self.add_line("No notes saved yet.", MUTED)

        self.add_line("")
        self.add_line('Example: "Remember to check the basil tomorrow"', MUTED)

    # --------------------------------------
    # CHAT
    # --------------------------------------

    def send_message(self, event=None):
        text = self.input.get().strip()

        if not text:
            return

        self.input.delete(0, "end")
        self.add_message("YOU", text)

        self.root.config(cursor="watch")
        self.root.update_idletasks()

        try:
            response = process(text, project_id=self.active_project_id)
        except Exception as error:
            response = f"Something went wrong: {error}"

        self.root.config(cursor="")
        self.add_message("KUGEL", str(response))

        # Refresh the currently selected view after a command.
        if self.current_view == "KUGEL OVERVIEW":
            self.show_overview()
        elif self.current_view == "TASKS":
            self.show_tasks()
        elif self.current_view == "PROJECTS":
            self.show_projects()
        elif self.current_view == "CALENDAR":
            self.show_calendar()
        elif self.current_view == "NOTES":
            self.show_notes()
        elif self.current_view == "PROJECT_DETAIL" and self.active_project_id is not None:
            self.open_project(self.active_project_id)

    # --------------------------------------
    # CLOCK
    # --------------------------------------

    def update_clock(self):
        self.clock.config(
            text=datetime.now().strftime("%d.%m.%Y  |  %H:%M:%S")
        )

        self.root.after(1000, self.update_clock)

    # --------------------------------------
    # CLOCK
    # --------------------------------------

    def update_clock(self):
        self.clock.config(
            text=datetime.now().strftime("%d.%m.%Y  |  %H:%M:%S")
        )

        self.root.after(1000, self.update_clock)


# ==========================================
# START KUGEL DESKTOP
# ==========================================

if __name__ == "__main__":
    root = tk.Tk()
    app = KugelDesktop(root)
    root.mainloop()