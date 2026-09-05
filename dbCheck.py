from database import get_connection

conn = get_connection()
cursor = conn.cursor()

print("\n--- TODOS ---")
cursor.execute("SELECT * FROM todos")
for row in cursor.fetchall():
    print(row)

print("\n--- NOTES ---")
cursor.execute("SELECT * FROM notes")
for row in cursor.fetchall():
    print(row)

print("\n--- PROJECTS ---")
cursor.execute("SELECT * FROM projects")
for row in cursor.fetchall():
    print(row)

conn.close()