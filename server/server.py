import socket
import threading
import json
import time

HOST = "127.0.0.1"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Server started...")

clients = []
players = {}   # conn → username
answers = {}   # username → answer


# 🔹 Broadcast to all clients
def broadcast(message):
    for c in clients[:]:   # copy list to avoid issues
        try:
            c.send(message.encode())
        except:
            clients.remove(c)


# 🔹 Handle each client
def handle_client(conn, addr):
    print("Connected:", addr)

    try:
        # JOIN message
        data = conn.recv(1024).decode()
        parts = data.split("|", 1)

        if len(parts) != 2:
            return

        msg_type, username = parts

        if msg_type == "JOIN":
            players[conn] = username
            print(username, "joined")

        # Listen for answers
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            parts = data.split("|", 1)
            if len(parts) != 2:
                continue

            msg_type, content = parts

            if msg_type == "ANSWER":
                answers[players[conn]] = content
                print(players[conn], "answered:", content)

    except:
        pass

    finally:
        conn.close()
        if conn in clients:
            clients.remove(conn)
        if conn in players:
            print(players[conn], "disconnected")
            del players[conn]


# 🔹 Accept clients
def accept_clients():
    while True:
        conn, addr = server.accept()
        clients.append(conn)

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


# Start accepting clients
threading.Thread(target=accept_clients, daemon=True).start()

print("Waiting for players...")
input("Press Enter AFTER all players join...")


# 🔹 Load questions
with open("data/questions.json") as f:
    questions = json.load(f)


# 🔹 QUIZ LOOP
for q in questions:

    answers.clear()

    question = q["question"]

    print("\nSending question:", question)
    broadcast(f"QUESTION|{question}")

    time.sleep(1)

    # Wait for answers
    wait_time = 10
    start = time.time()

    while time.time() - start < wait_time:
        if len(answers) == len(players):
            break
        time.sleep(0.1)

    # Results
    print("\n--- Results ---")
    for player, ans in answers.items():
        print(f"{player} → {ans}")

    # Correct answer
    correct = q["answer"]
    print(f"Correct Answer: {correct}")

    # Send to clients
    broadcast(f"RESULT|Correct answer: {correct}")
    broadcast("INFO|Next question coming...")

    time.sleep(2)


# End quiz
broadcast("END|Quiz finished")
print("Quiz ended")