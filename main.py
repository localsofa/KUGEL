from config import AUDIO_MODE
from database import init_database
from brain import process

if AUDIO_MODE:
    from audio import listen


init_database()

print("KUGEL online.")

while True:

    # -------------------
    # AUDIO MODE
    # -------------------

    if AUDIO_MODE:

        input("\nPress ENTER to talk...")

        user_text = listen()

        print(f"You: {user_text}")

    # -------------------
    # TEXT MODE
    # -------------------

    else:

        user_text = input("\nYou: ")

    # -------------------
    # EXIT
    # -------------------

    if user_text.lower() in ["exit", "quit", "bye", "goodbye", "tschüss", "pfirti"]:

        print("KUGEL: Goodbye.")
        break

    # -------------------
    # BRAIN
    # -------------------

    response = process(user_text)

    print(f"KUGEL: {response}")