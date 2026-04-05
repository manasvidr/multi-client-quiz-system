from game_logic.scoring import check_answer
from game_logic.leaderboard import generate_leaderboard
import socket
import threading
import json
import time
from scoring import check_answers, update_scores
from leaderboard import generate_leaderboard, format_leaderboard

HOST = "127.0.0.1"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Server started...")

clients = []
players = {}   # conn → username
player_scores = {}  # username → {score}
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
            layer_scores[username] = {"score": 0}
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
                answers[players[conn]] = (content, time.time())
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
    question_start_time = time.time()

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

    correct = q["answer"]

    scores = {}

    for player, ans in answers.items():
<<<<<<< Updated upstream
        print(f"{player} → {ans}")
    processed_answers = {}
=======
     is_correct = check_answer(ans, correct)

    if is_correct:
        scores[player] = 10
    else:
        scores[player] = 0

    print(f"{player} → {ans} ({'Correct' if is_correct else 'Wrong'})")


# Generate leaderboard
    leaderboard = generate_leaderboard(scores)

    print("\nLeaderboard:", leaderboard)

# Send to clients
    broadcast(f"SCORE|{leaderboard}")
>>>>>>> Stashed changes

    for player, (ans, timestamp) in answers.items():
        time_taken = round(timestamp - question_start_time, 2)
        processed_answers[player] = (ans, time_taken)
    # Correct answer
    correct = q["answer"]
    print(f"Correct Answer: {correct}")

    
    # --- SCORING (YOUR PART) ---
    results = check_answers(correct, processed_answers)

    update_scores(player_scores, results)

    leaderboard = generate_leaderboard(player_scores)

    score_msg = format_leaderboard(leaderboard)

    print("Leaderboard:", score_msg)

    broadcast(score_msg)

    # Send to clients
    broadcast(f"RESULT|Correct answer: {correct}")
    broadcast("INFO|Next question coming...")

    time.sleep(2)


# End quiz
broadcast("END|Quiz finished")
print("Quiz ended")
