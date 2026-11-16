# KUGEL
* small home assistant project i've been messing around with
* pretty clunky atm, but will later on be connected to a raspberry pi and esp32
* features like automatic watering etc will happen whenever i have time (and resources) :)
* currently working on transcription & audio mode
* **features to add:** set "goal" for the session; kugel highlights the most important to dos & any relevant emails for it
* **fixed to do:** ollama email summarization 

# main.py
- execution of all helper functions
- interaction

# brain.py
- intent recognition
- keyword recognition

# audio.py
- transcription & audio mode
- UNTESTED

# database.py
- save to SQLite

# config.py
- toggle model & audio mode

# actions.py
- all helper function triggered upon intent recognition
- current: create_project, create_todo, list_todos, create_note

# llm.py
- ollama prompts

# dbCheck.py
- debug to test database

# Outlook notifications
- The desktop orb can check a personal Outlook.com inbox or a Microsoft 365 work account every 10 minutes using Microsoft Graph. A GoDaddy-hosted address must be a Microsoft 365/Exchange Online mailbox; GoDaddy Workspace Email is not supported by Microsoft Graph.
- Routine checks read message IDs, sender, and subject; the first check establishes a baseline and does not notify for existing mail. On startup, KUGEL also fetches the five latest emails (or fewer if the inbox has fewer) and summarizes them locally with the configured Ollama model.
- Ollama must be running locally with the configured model available for the startup email summary. If the inbox is empty, KUGEL says so without calling the model.
- Install dependencies with `python -m pip install -r requirements.txt`.
- In the Microsoft Entra admin center, register a public client app for **Accounts in any organizational directory and personal Microsoft accounts**. Add the Mobile and desktop applications platform with redirect URI `http://localhost`, enable public client flows, and add delegated Microsoft Graph `Mail.Read`.
- Right-click the orb, choose **Connect Outlook**, and enter the app's Application (client) ID. Use **Switch Outlook account** to sign in to a different mailbox, or **Change Outlook client ID** to replace a previously saved ID. After a successful inbox check, KUGEL confirms the connection and checks for new mail every 10 minutes. KUGEL reuses the saved sign-in on later launches and only opens Microsoft sign-in when interactive authentication is needed (or when you switch accounts); it never asks for or stores your email password. Microsoft may require sign-in again if the saved session is revoked or expires.
- The client ID and a Windows-user-protected sign-in token cache are stored under `%LOCALAPPDATA%\KUGEL`.

# Desktop companion
- Run `python kugel_orb.py` to launch the floating companion.
- The orb uses `IdleKugel.gif` for its idle animation and `kugelSprite.png` as a static fallback when animated transparency is unavailable.

# Project workspaces
- In the desktop dashboard, open **PROJECTS** and click a project to edit its overview and next action, capture notes, save web links, and manage project tasks.
- While a project is open, chat commands such as `Remember ...` and `Add todo ...` save directly to that project. You can also target one by name: `Add idea to project Greenhouse: ...`, `Add link to project Greenhouse: Planning doc | https://example.com`, or `Add task to project Greenhouse: Order seeds`.
- **KUGEL SUMMARY** and **NEXT STEPS** use the configured local Ollama model and the selected project's overview, notes, links, and open tasks. Chat commands `Summarize project Greenhouse` and `Suggest next steps for project Greenhouse` work without opening its page.