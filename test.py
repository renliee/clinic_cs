from chatbot import handle_message

user_id = "test_user"

while True:
    msg = input("Customer: ").strip()
    if msg == 'q':
        break

    response = handle_message(user_id, msg)
    print(f"Bot: {response}\n")