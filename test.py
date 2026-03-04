# from main import handle_message

# user_id = "test_user"

# while True:
#     msg = input("Customer: ").strip()
#     if msg == 'q':
#         break

#     response = handle_message(user_id, msg)
#     print(f"Bot: {response}\n")

# test.py
try:
    from main import handle_message
except Exception as e:
    print("Failed importing handler:", e)
    raise SystemExit(1)

user_id = "test_user"
while True:
    try:
        msg = input("Customer: ").strip()
    except KeyboardInterrupt:
        print("\nInterrupted (Ctrl+C). Type 'q' to quit.")
        continue
    if msg == 'q':
        break
    response = handle_message(user_id, msg)
    print(f"Bot: {response}\n")