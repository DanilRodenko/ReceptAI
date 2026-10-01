from pipeline import new_session, handle_turn, now_local

session = new_session()

while True:
    text = input("You: ").strip()
    if not text:
        break
    reply = handle_turn(session, text, now_local())
    print(f"Sarah: {reply}")
    print(f"[state: {session['state']}]")
    print(f"[draft: {session['draft']}]")