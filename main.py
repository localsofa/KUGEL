from router import process

print("KUGEL online. Servus!\n")

while True:
    user = input("You: ")

    if user.lower() in ["exit", "quit"]:
        print("KUGEL: bye! :)")
        break

    response = process(user)

    print("KUGEL:", response)