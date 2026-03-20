import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 5000   # use teammate's port


# ----------------------------
# CONNECTION
# ----------------------------
def connect_to_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print("Connected to server!")
    return client


# ----------------------------
# USER LOGIN
# ----------------------------
def send_username(client):
    username = input("Enter your username: ")
    client.send(f"JOIN|{username}".encode())


# ----------------------------
# TIMER
# ----------------------------
def countdown_timer(seconds):
    for i in range(seconds, 0, -1):
        print(f"Time remaining: {i}s", end="\r")
        time.sleep(1)


# ----------------------------
# HANDLE QUESTION
# ----------------------------
def handle_question(client, question):
    print("\n----------------------")
    print("QUESTION")
    print("----------------------")
    print(question)

    timer_thread = threading.Thread(target=countdown_timer, args=(10,))
    timer_thread.start()

    answer = input("\nYour answer: ")
    client.send(f"ANSWER|{answer}".encode())


# ----------------------------
# HANDLE MESSAGES
# ----------------------------
def handle_message(client, data):
    try:
        msg_type, content = data.split("|", 1)
    except:
        print("Invalid message:", data)
        return True

    if msg_type == "QUESTION":
        handle_question(client, content)

    elif msg_type == "RESULT":
        print("\n✔ RESULT:", content)

    elif msg_type == "INFO":
        print("\nℹ", content)

    elif msg_type == "SCORE":
        print("\n🏆 LEADERBOARD")
        players = content.split(",")
        for i, p in enumerate(players, 1):
            print(f"{i}. {p}")

    elif msg_type == "END":
        print("\n======================")
        print(content)
        print("======================")
        return False

    else:
        print("\n[UNKNOWN]", data)

    return True


# ----------------------------
# RECEIVE LOOP
# ----------------------------
def receive_messages(client):
    while True:
        try:
            data = client.recv(1024).decode()

            if not data:
                break

            print("DEBUG:", data)  # helpful for now

            keep_running = handle_message(client, data)

            if not keep_running:
                break

        except:
            break


# ----------------------------
# MAIN
# ----------------------------
def main():
    try:
        client = connect_to_server()
        send_username(client)

        receive_messages(client)

    except ConnectionRefusedError:
        print("Server not running.")

    finally:
        print("Disconnecting...")
        client.close()


if __name__ == "__main__":
    main()