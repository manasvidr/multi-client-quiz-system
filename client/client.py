# client/client.py

import socket
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game_logic.leaderboard import display_leaderboard

HOST = "127.0.0.1"
PORT = 5555

current_question = None
waiting_for_answer = False
client_socket = None
current_options = []


def connect_to_server(host: str, port: int) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s


def send_message(sock: socket.socket, message: str):
    sock.sendall((message + "\n").encode())


def send_answer(sock: socket.socket, answer: str):
    send_message(sock, f"ANSWER|{answer}")


def receive_question(message: str):
    global current_question, waiting_for_answer, current_options
    parts = message.split("|", 1)[1]

    # Options are sent as: QUESTION|<question text>|<opt1>,<opt2>,<opt3>,<opt4>
    if "||" in parts:
        question_text, options_str = parts.split("||", 1)
        current_options = options_str.split(",")
    else:
        question_text = parts
        current_options = []

    current_question = question_text
    waiting_for_answer = True

    print(f"\n  {'─'*50}")
    print(f"  [Q] {question_text}")
    if current_options:
        labels = ["A", "B", "C", "D"]
        for i, opt in enumerate(current_options):
            label = labels[i] if i < len(labels) else str(i + 1)
            print(f"      {label}) {opt.strip()}")
    print(f"  {'─'*50}")
    print("  Your answer: ", end="", flush=True)


def handle_server_message(message: str):
    global waiting_for_answer, current_question

    if message.startswith("ACK|"):
        print(f"\n  {message.split('|', 1)[1]}")

    elif message.startswith("INFO|"):
        info = message.split('|', 1)[1]
        print(f"\n  [INFO] {info}")
        # Do NOT reprint "Your answer:" here to avoid duplication

    elif message.startswith("QUESTION|"):
        receive_question(message)

    elif message.startswith("TIMER|"):
        secs = message.split("|", 1)[1]
        print(f"  [TIMER] You have {secs} seconds to answer!")
        # Only print prompt once; question handler already did it
        if waiting_for_answer:
            print("  Your answer: ", end="", flush=True)

    elif message.startswith("RESULT|"):
        waiting_for_answer = False
        current_question = None
        result = message.split("|", 1)[1]
        print(f"\n  [RESULT] {result}")

    elif message.startswith("SCORE|"):
        display_leaderboard(message)

    elif message.startswith("ERROR|"):
        print(f"\n  [ERROR] {message.split('|', 1)[1]}")
        sys.exit(1)

    elif message.startswith("END|"):
        print(f"\n  {message.split('|', 1)[1]}")
        print("  Game over. Goodbye!\n")
        sys.exit(0)

    else:
        print(f"\n  [Server] {message}")


def listen_to_server(sock: socket.socket):
    buffer = ""
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                print("\n  [Client] Server closed connection.")
                sys.exit(0)
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    handle_server_message(line)
        except Exception as e:
            print(f"\n  [Client] Connection error: {e}")
            sys.exit(1)


def main():
    global client_socket

    host = sys.argv[1] if len(sys.argv) >= 2 else HOST
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else PORT

    print("\n" + "=" * 52)
    print("          WELCOME TO THE QUIZ GAME 🎯")
    print("=" * 52)

    username = input("  Enter your username: ").strip()
    if not username:
        print("  Username cannot be empty.")
        sys.exit(1)

    try:
        client_socket = connect_to_server(host, port)
        print(f"  [Client] Connected to server at {host}:{port}")
    except Exception as e:
        print(f"  [Client] Could not connect: {e}")
        sys.exit(1)

    send_message(client_socket, f"JOIN|{username}")

    listener = threading.Thread(target=listen_to_server, args=(client_socket,), daemon=True)
    listener.start()

    while True:
        try:
            user_input = input()
            if waiting_for_answer and user_input.strip():
                send_answer(client_socket, user_input.strip())
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n  [Client] Disconnected.")
            break

    client_socket.close()


if __name__ == "__main__":
    main()
