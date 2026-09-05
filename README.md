# KUGEL
* small home assistant project i've been messing around with
* pretty clunky atm, but will later on be connected to a raspberry pi and esp32
* features like automatic watering etc will happen whenever i have time (and resources) :)
* currently working on transcription & audio mode

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