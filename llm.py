import json
import requests

from config import OLLAMA_MODEL


def classify_intent(text):

    prompt = f"""
Classify the user's message into exactly ONE intent.

Available intents:

- todo_create
- todo_list
- note_create
- project_create
- chat

Return ONLY valid JSON.

Rules:

todo_create:
The user wants to create or add a task.

todo_list:
The user wants to see their tasks.

note_create:
The user wants KUGEL to remember information.

project_create:
The user wants to create a project.

chat:
Everything else.

User message:
{text}

Return this format:

{{
    "intent": "intent_name",
    "content": "relevant content"
}}
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0
                }
            },
            timeout=60
        )

        response.raise_for_status()

        raw = response.json()["response"]

        print(f"[DEBUG] Raw LLM: {raw}")

        return json.loads(raw)

    except Exception as error:

        print(f"[DEBUG] LLM ERROR: {error}")

        return {
            "intent": "chat",
            "content": text
        }