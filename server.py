import socket
import threading
import hashlib
import base64
from cryptography.fernet import Fernet
import json
import time


BIND_PORT = 60000
SECRET_KEY = "super_secret_key"
HARDCODED_DISTANCE = 24

players_positions = {}

def generate_key(x, y, secret, distance):
    combined = f"{x}{y}{secret}{distance}".encode()
    hash_value = hashlib.sha256(combined).digest()
    return base64.urlsafe_b64encode(hash_value[:32])

def encrypt_coordinates(target_x, target_y, distance):
    key = generate_key(target_x, target_y, SECRET_KEY, distance)
    f = Fernet(key)
    coordinates = f"{target_x},{target_y}".encode()
    encrypted_coordinates = f.encrypt(coordinates)
    return json.dumps({'data': base64.b64encode(encrypted_coordinates).decode()})

def handle_client(conn, addr):
    global players_positions
    print(f"Connected by {addr}")

    player_id = None

    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            player_data = json.loads(data)
            player_id = player_data['id']
            player_x = player_data['x']
            player_y = player_data['y']
            distance = HARDCODED_DISTANCE

            # update the player's position
            players_positions[player_id] = (player_x, player_y)

            # encrypt all of the player positions
            encrypted_positions = {}
            for pid, (x, y) in players_positions.items():
                encrypted_positions[pid] = encrypt_coordinates(x, y, distance)

            # send encrypted positions back to the client
            conn.send(json.dumps(encrypted_positions).encode())

        except ConnectionResetError:
            print(f"Player {player_id} disconnected.")
            break

    if player_id:
        # remove any disconnected player from the list
        del players_positions[player_id]
        print(f"Player {player_id} removed from positions list.")

    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', BIND_PORT))
    server.listen()

    print("Server is listening...")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Active connections: {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()
