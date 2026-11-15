import tkinter as tk
import calendar as pycalendar
import tkinter.font as tkfont

from tkinter import simpledialog, messagebox
from datetime import datetime, date

from brain import process
from database import get_connection, init_database
from actions import complete_todo


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

def fetch_rows(query):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
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
        SELECT name
        FROM projects
        ORDER BY created_at DESC
        LIMIT 8
    """)


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

    def add_section(self, title):
        tk.Label(
            self.content,
            text=title,
            font=FONT_BOLD,
            fg=GREEN,
            bg=BG
        ).pack(anchor="w", pady=(12, 5))

    def add_line(self, text, color=TEXT):
        tk.Label(
            self.content,
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
            for (name,) in projects:
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
        self.clear_content("PROJECTS")

        self.add_section("ACTIVE PROJECTS")
        projects = get_projects()

        if projects:
            for (name,) in projects:
                self.add_line(f"> {name}")
        else:
            self.add_line("No projects created yet.", MUTED)

        self.add_line("")
        self.add_line("Tip: use the chat to create a project.")
        self.add_line('Example: "Create project Greenhouse Mk1"', MUTED)

    # --------------------------------------
    # CALENDAR
    # --------------------------------------

    def show_calendar(self):
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
            response = process(text)
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