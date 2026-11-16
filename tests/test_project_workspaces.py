import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from actions import (
    find_project,
    get_project_context,
    save_project_link,
    save_project_note,
)
from brain import process


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"response": "Break the work into a few small steps."}


class ProjectWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "kugel.db"

        conn = sqlite3.connect(database.DB_PATH)
        conn.executescript("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO projects (name) VALUES ('Garden');
            INSERT INTO todos (task) VALUES ('Existing task');
        """)
        conn.commit()
        conn.close()
        database.init_database()
        self.project_id = find_project("garden")[0]

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_existing_database_migrates_and_keeps_project_data(self):
        conn = database.get_connection()
        try:
            project_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(projects)")
            }
            todo_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(todos)")
            }
            existing_task = conn.execute(
                "SELECT task, project_id FROM todos WHERE task = 'Existing task'"
            ).fetchone()
        finally:
            conn.close()

        self.assertIn("description", project_columns)
        self.assertIn("next_action", project_columns)
        self.assertIn("project_id", todo_columns)
        self.assertEqual(existing_task, ("Existing task", None))

    def test_project_capture_context_and_local_assistant(self):
        self.assertIn("idea", process(
            "Add idea to project Garden: Build a small greenhouse"
        ))
        self.assertIn("link", process(
            "Add link to project Garden: Growing guide | https://example.com/guide"
        ))
        self.assertIn("project", process(
            "Add task to project Garden: Compare greenhouse kits"
        ))
        self.assertIn("project", process(
            "Remember measure the sunny wall",
            project_id=self.project_id
        ))

        conn = database.get_connection()
        try:
            note_id = conn.execute(
                "SELECT id FROM project_notes WHERE content = ?",
                ("Build a small greenhouse",)
            ).fetchone()[0]
            link_id = conn.execute(
                "SELECT id FROM project_links WHERE title = ?",
                ("Growing guide",)
            ).fetchone()[0]
        finally:
            conn.close()
        save_project_note(
            self.project_id,
            "Build a greenhouse with a recycled window",
            note_id
        )
        save_project_link(
            self.project_id,
            "Updated growing guide",
            "https://example.com/new-guide",
            link_id
        )

        context = get_project_context(self.project_id)
        self.assertIn("recycled window", context)
        self.assertIn("https://example.com/new-guide", context)
        self.assertIn("Compare greenhouse kits", context)
        self.assertIn("measure the sunny wall", context)

        with patch("llm.requests.post", return_value=FakeResponse()) as post:
            result = process("Suggest next steps for project Garden")

        self.assertIn("small steps", result)
        prompt = post.call_args.kwargs["json"]["prompt"]
        self.assertIn("recycled window", prompt)
        self.assertIn("Compare greenhouse kits", prompt)

    def test_project_links_reject_non_web_urls(self):
        with self.assertRaisesRegex(ValueError, "http:// or https://"):
            process("Add link to project Garden: file:///private/data")


if __name__ == "__main__":
    unittest.main()
