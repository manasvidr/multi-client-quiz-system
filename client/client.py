import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

username = input("Enter your name: ")
client.send(f"JOIN|{username}".encode())


def receive():
    while True:
        try:
            data = client.recv(1024).decode()
            msg_type, content = data.split("|")

            if msg_type == "QUESTION":
                print("\nQuestion:", content)
                answer = input("Your answer: ")
                client.send(f"ANSWER|{answer}".encode())

            elif msg_type == "RESULT":
                print(content)

            elif msg_type == "INFO":
                print(content)

            elif msg_type == "END":
                print(content)
                break

        except:
            break


threading.Thread(target=receive).start()