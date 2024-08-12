import socket
import hashlib
import base64
from cryptography.fernet import Fernet
import json
import math
import random
import tkinter as tk

SECRET_KEY = "super_secret_key"
SERVER_IP = 'localhost'
SERVER_PORT = 60000

# constants for the new grid system
GRID_SIZE = 128
CANVAS_SIZE = 500
BLOCK_SIZE = CANVAS_SIZE // GRID_SIZE
DOT_RADIUS = 6  # adjusted to match the new block size
UPDATE_INTERVAL = 32  # interval in ms for sending/receiving data

def generate_key(x, y, secret, distance):
    combined = f"{x}{y}{secret}{distance}".encode()
    hash_value = hashlib.sha256(combined).digest()
    return base64.urlsafe_b64encode(hash_value[:32])

def decrypt_coordinates(player_x, player_y, encrypted_data):
    try:
        parsed_data = json.loads(encrypted_data)
        encrypted_coordinates = base64.b64decode(parsed_data['data'])

        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                possible_x = player_x + dx
                possible_y = player_y + dy
                key = generate_key(possible_x, possible_y, SECRET_KEY, distance)
                f = Fernet(key)
                try:
                    decrypted_coordinates = f.decrypt(encrypted_coordinates)
                    target_x, target_y = map(int, decrypted_coordinates.decode().split(','))
                    if is_within_distance(player_x, player_y, target_x, target_y, distance):
                        return target_x, target_y
                except:
                    continue
    except:
        return None

def is_within_distance(x1, y1, x2, y2, max_distance):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2) <= max_distance

class ClientApp:
    def __init__(self, master, player_id, player_x, player_y, distance):
        self.master = master
        self.player_id = player_id
        self.player_x = player_x
        self.player_y = player_y
        self.distance = distance
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_IP, SERVER_PORT))

        self.canvas = tk.Canvas(master, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="black")
        self.canvas.pack()

        self.player_dot = None
        self.sight_circle = None
        self.other_players_dots = {}

        self.update_position()

        self.movement = {"Up": False, "Down": False, "Left": False, "Right": False}

        self.master.bind("<Up>", lambda event: self.start_move("Up"))
        self.master.bind("<Down>", lambda event: self.start_move("Down"))
        self.master.bind("<Left>", lambda event: self.start_move("Left"))
        self.master.bind("<Right>", lambda event: self.start_move("Right"))

        self.master.bind("<KeyRelease-Up>", lambda event: self.stop_move("Up"))
        self.master.bind("<KeyRelease-Down>", lambda event: self.stop_move("Down"))
        self.master.bind("<KeyRelease-Left>", lambda event: self.stop_move("Left"))
        self.master.bind("<KeyRelease-Right>", lambda event: self.stop_move("Right"))

        self.update_loop()  # start the update loop
        self.move_loop()    # start the movement loop

    def update_position(self):
        if self.player_dot:
            self.canvas.delete(self.player_dot)
        if self.sight_circle:
            self.canvas.delete(self.sight_circle)

        self.sight_circle = self.canvas.create_oval(
            (self.player_x - self.distance) * BLOCK_SIZE, (self.player_y - self.distance) * BLOCK_SIZE,
            (self.player_x + self.distance) * BLOCK_SIZE, (self.player_y + self.distance) * BLOCK_SIZE,
            outline="", fill="grey", stipple="gray50"
        )

        self.player_dot = self.canvas.create_oval(
            self.player_x * BLOCK_SIZE - DOT_RADIUS, self.player_y * BLOCK_SIZE - DOT_RADIUS,
            self.player_x * BLOCK_SIZE + DOT_RADIUS, self.player_y * BLOCK_SIZE + DOT_RADIUS, fill="red"
        )

    def start_move(self, direction):
        self.movement[direction] = True

    def stop_move(self, direction):
        self.movement[direction] = False

    def move_loop(self):
        if self.movement["Up"]:
            self.player_y = max(0, self.player_y - 1)
        if self.movement["Down"]:
            self.player_y = min(GRID_SIZE - 1, self.player_y + 1)
        if self.movement["Left"]:
            self.player_x = max(0, self.player_x - 1)
        if self.movement["Right"]:
            self.player_x = min(GRID_SIZE - 1, self.player_x + 1)

        self.update_position()
        self.master.after(UPDATE_INTERVAL, self.move_loop)  # schedule the next movement update

    def update_loop(self):
        self.send_player_data()
        self.receive_and_update_positions()
        self.master.after(UPDATE_INTERVAL, self.update_loop)  # schedule the next update

    def send_player_data(self):
        player_data = {
            'id': self.player_id,
            'x': self.player_x,
            'y': self.player_y,
        }
        self.client_socket.send(json.dumps(player_data).encode())

    def receive_and_update_positions(self):
        encrypted_data = self.client_socket.recv(1024).decode()
        encrypted_positions = json.loads(encrypted_data)

        # clear old dots first
        for dot in self.other_players_dots.values():
            self.canvas.delete(dot)
        self.other_players_dots.clear()

        for pid, enc_data in encrypted_positions.items():
            if pid != self.player_id:
                decrypted_position = decrypt_coordinates(self.player_x, self.player_y, enc_data)
                if decrypted_position:
                    x, y = decrypted_position
                    self.other_players_dots[pid] = self.canvas.create_oval(
                        x * BLOCK_SIZE - DOT_RADIUS, y * BLOCK_SIZE - DOT_RADIUS,
                        x * BLOCK_SIZE + DOT_RADIUS, y * BLOCK_SIZE + DOT_RADIUS, fill="#79e0ed"
                    )

if __name__ == "__main__":
    player_id = input("Enter your player ID: ")

    player_x = random.randint(0, GRID_SIZE - 1)
    player_y = random.randint(0, GRID_SIZE - 1)
    print(f"Starting position for {player_id}: (X: {player_x}, Y: {player_y})")

    distance = 72

    root = tk.Tk()
    app = ClientApp(root, player_id, player_x, player_y, distance)
    root.mainloop()
