# server/server.py

import socket
import threading
import json
import random
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_logic.scoring import check_answer, update_score
from game_logic.leaderboard import generate_leaderboard

HOST = "0.0.0.0"
PORT = 5555
MIN_PLAYERS = 2
MAX_PLAYERS = 10
QUESTION_TIMEOUT = 15
QUESTIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "questions.json")

clients = {}
scores = {}
lock = threading.Lock()
game_started = False

# Per-round state — replaced each round, not a global accumulator
current_round_answers = {}
current_round_event = threading.Event()


def load_questions() -> list:
    with open(QUESTIONS_FILE, "r") as f:
        data = json.load(f)
    return random.sample(data, 10)


def send_to(conn, message: str):
    try:
        conn.sendall((message + "\n").encode())
    except Exception:
        pass


def broadcast(message: str, exclude=None):
    with lock:
        for conn in list(clients.keys()):
            if conn != exclude:
                send_to(conn, message)


def accept_clients(server_socket):
    print(f"[Server] Waiting for players on {HOST}:{PORT}...")
    while True:
        try:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_join, args=(conn, addr), daemon=True).start()
        except OSError:
            break


def handle_join(conn, addr):
    global game_started
    try:
        data = conn.recv(1024).decode().strip()
        if not data.startswith("JOIN|"):
            conn.close()
            return

        username = data.split("|", 1)[1].strip()

        with lock:
            if game_started:
                send_to(conn, "ERROR|Game already in progress. Please wait for next round.")
                conn.close()
                return
            if len(clients) >= MAX_PLAYERS:
                send_to(conn, f"ERROR|Server is full ({MAX_PLAYERS} players max).")
                conn.close()
                return
            if username in clients.values():
                send_to(conn, "ERROR|Username already taken")
                conn.close()
                return
            clients[conn] = username
            scores[username] = 0

        print(f"[Server] '{username}' joined from {addr}")
        send_to(conn, f"ACK|Welcome {username}! Waiting for game to start... ({len(clients)}/{MIN_PLAYERS} needed)")
        broadcast(f"INFO|{username} has joined! ({len(clients)}/{MIN_PLAYERS} players)", exclude=conn)

        handle_client_answers(conn, username)

    except Exception as e:
        print(f"[Server] Error handling join: {e}")
        with lock:
            clients.pop(conn, None)
        conn.close()


def handle_client_answers(conn, username):
    buffer = ""
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line.startswith("ANSWER|"):
                    answer = line.split("|", 1)[1]
                    answer_time = time.time()
                    with lock:
                        # Only record first answer per player per round
                        if username not in current_round_answers:
                            current_round_answers[username] = (answer, answer_time)
                            print(f"[Server] Answer from '{username}': {answer}")
                        # Signal if all active clients have answered
                        if len(current_round_answers) >= len(clients):
                            current_round_event.set()
        except Exception:
            break

    print(f"[Server] '{username}' disconnected.")
    with lock:
        clients.pop(conn, None)
        # If remaining clients have all answered, unblock the round
        if clients and len(current_round_answers) >= len(clients):
            current_round_event.set()


def broadcast_question(question: str):
    broadcast(f"QUESTION|{question}")



def broadcast_question(question: str, options: list = None):
    if options:
        options_str = ",".join(options)
        broadcast(f"QUESTION|{question}||{options_str}")
    else:
        broadcast(f"QUESTION|{question}")


def receive_answers(timeout: float) -> dict:
    global current_round_answers
    with lock:
        current_round_answers = {}
        current_round_event.clear()

    deadline = time.time() + timeout
    current_round_event.wait(timeout=timeout)

    result = {}
    with lock:
        for username, (ans, answer_time) in current_round_answers.items():
            time_remaining = max(0, deadline - answer_time)
            result[username] = (ans, time_remaining)

    return result


def send_results():
    msg = generate_leaderboard(scores)
    broadcast(msg)
    print(f"[Server] Sent leaderboard: {msg}")


def run_quiz(questions: list):
    global game_started
    game_started = True

    print(f"\n[Server] Quiz starting with {len(clients)} players!\n")
    broadcast("INFO|Quiz is starting NOW! Get ready...")
    time.sleep(2)

    for i, q in enumerate(questions, 1):
        question_text = q["question"]
        correct_answer = q["answer"]
        acceptable = q.get("acceptable", None)

        print(f"\n[Server] Q{i}: {question_text} | Answer: {correct_answer}")
        broadcast(f"INFO|Question {i} of {len(questions)}")
       
        broadcast_question(question_text, q.get("options", []))

        if acceptable:
            hints = ", ".join(acceptable)
            broadcast(f"INFO|Acceptable answers include: {hints}")

        broadcast(f"TIMER|{QUESTION_TIMEOUT}")

        received = receive_answers(timeout=QUESTION_TIMEOUT)

        with lock:
            current_clients = dict(clients)

        for conn, username in current_clients.items():
            if username in received:
                answer, time_remaining = received[username]
                correct = check_answer(answer, correct_answer, acceptable)
                update_score(scores, username, correct, time_remaining)
                status = "✓ Correct" if correct else "✗ Wrong"
                send_to(conn, f"RESULT|{status}! Answer was: {correct_answer}")
            else:
                send_to(conn, f"RESULT|Time's up! Answer was: {correct_answer}")

        send_results()
        time.sleep(3)

    broadcast("INFO|Quiz Over! Final scores:")
    send_results()
    broadcast("END|Thanks for playing!")
    print("\n[Server] Quiz complete.")


def start_server():
    global MIN_PLAYERS, MAX_PLAYERS

    if len(sys.argv) >= 2:
        try:
            MIN_PLAYERS = int(sys.argv[1])
        except ValueError:
            pass
    if len(sys.argv) >= 3:
        try:
            MAX_PLAYERS = int(sys.argv[2])
        except ValueError:
            pass

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_PLAYERS)

    print(f"[Server] Started on {HOST}:{PORT}")
    print(f"[Server] Waiting for {MIN_PLAYERS}–{MAX_PLAYERS} players...\n")

    accept_thread = threading.Thread(target=accept_clients, args=(server_socket,), daemon=True)
    accept_thread.start()

    while True:
        with lock:
            count = len(clients)
        if count >= MIN_PLAYERS:
            break
        time.sleep(1)

    print(f"[Server] {MIN_PLAYERS}+ players connected. Starting in 5 seconds...")
    broadcast(f"INFO|Enough players joined! Starting in 5 seconds...")
    time.sleep(5)

    questions = load_questions()
    run_quiz(questions)

    server_socket.close()


if __name__ == "__main__":
    start_server()
