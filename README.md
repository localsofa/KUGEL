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
- Routine checks read message IDs, sender, and subject; the first check establishes a baseline and does not notify for existing mail. On startup, KUGEL also fetches email previews from the past hour and summarizes them locally with the configured Ollama model.
- Ollama must be running locally with the configured model available for the startup email summary. If there are no recent emails, KUGEL says so without calling the model.
- Install dependencies with `python -m pip install -r requirements.txt`.
- In the Microsoft Entra admin center, register a public client app for **Accounts in any organizational directory and personal Microsoft accounts**. Add the Mobile and desktop applications platform with redirect URI `http://localhost`, enable public client flows, and add delegated Microsoft Graph `Mail.Read`.
- Right-click the orb, choose **Connect Outlook**, and enter the app's Application (client) ID. Use **Switch Outlook account** to sign in to a different mailbox, or **Change Outlook client ID** to replace a previously saved ID. After a successful inbox check, KUGEL confirms the connection and checks for new mail every 10 minutes. KUGEL opens a Microsoft sign-in page for consent; it never asks for or stores your email password.
- The client ID and a Windows-user-protected sign-in token cache are stored under `%LOCALAPPDATA%\KUGEL`.

# Desktop companion
- Run `python kugel_orb.py` to launch the floating companion.
- The orb uses `IdleKugel.gif` for its idle animation and `kugelSprite.png` as a static fallback when animated transparency is unavailable.