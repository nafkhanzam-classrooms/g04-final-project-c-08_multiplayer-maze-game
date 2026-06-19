import pygame
import socket
import threading
import json
import time
import random
import sys

# --- SERVER CONFIGURATION ---
HOST = '127.0.0.1'
PORT = 5555
MAX_PLAYERS = 4

# --- COLORS & DISPLAY FOR SPECTATOR ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MAZE_COLOR = (40, 44, 52)
PLAYER_COLORS = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]

class GameServer:
    def __init__(self):
        # Networking
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen(MAX_PLAYERS)
        self.players = {} # {addr: {'id': int, 'pos': [x,y], 'ready': bool, 'ping': 0, 'score': 0}}
        self.connections = {}
        self.player_counter = 0
        self.winner_id = None #manual
        self.winner_path = [] #manual
        
        # Game State
        self.state = "LOBBY" # LOBBY, COUNTDOWN, PLAYING, GAME_OVER
        self.game_mode = "Normal" # Normal mode
        self.maze = []
        self.start_pos = [1, 1]
        self.end_pos = [1, 1]
        self.replay_data = {} # {timestamp: {player_id: [x,y]}}
        self.start_time = 0
        
        # Spectator UI
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Server Spectator Mode")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

    def log(self, message):
        """Server activity log."""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def generate_maze(self, width, height):
        """ Authoritative maze generation on the server. """
        maze = [[1 for _ in range(width)] for _ in range(height)]
        def is_valid(x, y): return 0 < x < width-1 and 0 < y < height-1
        def carve_path(x, y):
            maze[y][x] = 0
            directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if is_valid(nx, ny) and maze[ny][nx] == 1:
                    maze[y + dy//2][x + dx//2] = 0
                    carve_path(nx, ny)

        carve_path(1, 1)
        self.start_pos = [1, 1]
        self.end_pos = [width-2, height-2]
        maze[self.start_pos[1]][self.start_pos[0]] = 2  # Start
        maze[self.end_pos[1]][self.end_pos[0]] = 3      # End
        self.maze = maze

    def handle_client(self, conn, addr):
        p_id = self.players[addr]['id']
        self.log(f"Player {p_id} joined from {addr}")
        
        # Send initial connection data
        init_data = {"type": "init", "id": p_id}
        conn.sendall((json.dumps(init_data) + "\n").encode())

        try:
            buffer = ""
            while True:
                data = conn.recv(2048).decode()
                if not data: break
                
                buffer += data
                while "\n" in buffer:
                    message_str, buffer = buffer.split("\n", 1)
                    if message_str.strip():
                        self.process_client_message(addr, json.loads(message_str), conn)
        except Exception as e:
            self.log(f"Error with Player {p_id}: {e}")
        finally:
            self.log(f"Player {p_id} disconnected.")
            del self.players[addr]
            del self.connections[addr]
            conn.close()

    def process_client_message(self, addr, msg, conn):
        p_id = self.players[addr]['id']
        msg_type = msg.get("type")

        if msg_type == "ping":
            # Echo back immediately for client to calculate RTT
            conn.sendall((json.dumps({"type": "pong", "time": msg["time"]}) + "\n").encode())
            # Also store the ping if the client sends their calculated ping
            if "latency" in msg:
                self.players[addr]['ping'] = msg["latency"]

        elif msg_type == "ready":
            self.players[addr]['ready'] = msg.get("status", True)
            self.game_mode = msg.get("mode", self.game_mode)
            self.log(f"Player {p_id} is ready.")
            self.check_start_conditions()

        elif msg_type == "move" and self.state == "PLAYING":
            dx, dy = msg.get("dx", 0), msg.get("dy", 0)
            curr_x, curr_y = self.players[addr]['pos']
            new_x, new_y = curr_x + dx, curr_y + dy
            
            # Server-side collision validation
            if 0 <= new_x < len(self.maze[0]) and 0 <= new_y < len(self.maze):
                if self.maze[new_y][new_x] != 1:
                    self.players[addr]['pos'] = [new_x, new_y]
                    
                    # Check win condition
                    if self.maze[new_y][new_x] == 3:
                        self.winner_id = p_id
                        self.log(f"Player {p_id} reached the end!")
                        print("WINNER SET TO", p_id)
                        self.state = "GAME_OVER"
        
        elif msg_type == "home":

            self.state = "LOBBY"

            self.maze = []

            self.replay_data = {}

            self.winner_id = None

            for p in self.players.values():
                p["ready"] = False
                p["pos"] = [1, 1]

    def check_start_conditions(self):
        if self.state != "LOBBY": return
        if len(self.players) == 0: return
        
        all_ready = all(p['ready'] for p in self.players.values())
        if all_ready:
            self.log("All players ready. Generating maze and starting countdown.")
            self.generate_maze(21, 21) # Fixed size for this round
            self.state = "COUNTDOWN"
            
            # Reset player positions
            for addr in self.players:
                self.players[addr]['pos'] = list(self.start_pos)
            
            # Send maze and state to all
            self.broadcast_state()
            threading.Timer(3.0, self.start_game).start()

    def start_game(self):
        self.state = "PLAYING"
        self.start_time = time.time()
        self.replay_data.clear()
        self.log("Game started!")

    def broadcast_state(self):
        """Sends the global state to all connected clients."""        
        state_msg = {
            "type": "update",
            "state": self.state,
            "mode": self.game_mode,
            "maze": self.maze if self.state in ["COUNTDOWN", "PLAYING", "GAME_OVER"] else None,
            "players": {p['id']: p for p in self.players.values()},
            "winner": self.winner_id,
            "winner_path": self.winner_path,
            "replay": self.replay_data if self.state == "GAME_OVER" else None
        }

        encoded_msg = (json.dumps(state_msg) + "\n").encode()
        for conn in self.connections.values():
            try:
                conn.sendall(encoded_msg)
                #print("Winner:", self.winner_id)
            except:
                pass # Handled by disconnect

    def record_replay(self):
        if self.state == "PLAYING":
            elapsed = round(time.time() - self.start_time, 2)
            positions = {p['id']: list(p['pos']) for p in self.players.values()}
            self.replay_data[elapsed] = positions

    def draw_spectator(self):
        self.screen.fill(BLACK)
        
        # Draw Maze
        if self.maze:
            cell_width = SCREEN_WIDTH // len(self.maze[0])
            cell_height = SCREEN_HEIGHT // len(self.maze)
            for y, row in enumerate(self.maze):
                for x, cell in enumerate(row):
                    rect = pygame.Rect(x * cell_width, y * cell_height, cell_width, cell_height)
                    if cell == 1: pygame.draw.rect(self.screen, MAZE_COLOR, rect)
                    elif cell == 2: pygame.draw.rect(self.screen, (0, 255, 0), rect)
                    elif cell == 3: pygame.draw.rect(self.screen, (255, 0, 0), rect)

        # Draw Players
        for addr, player in self.players.items():
            px, py = player['pos']
            color = PLAYER_COLORS[(player['id'] - 1) % len(PLAYER_COLORS)]
            
            if self.maze:
                p_rect = pygame.Rect(px * cell_width, py * cell_height, cell_width, cell_height)
                pygame.draw.circle(self.screen, color, p_rect.center, cell_width//3)
            
            # Overlay info
            info = self.font.render(f"P{player['id']} | Ping: {player['ping']}ms | Ready: {player['ready']}", True, color)
            self.screen.blit(info, (10, 10 + (player['id'] * 25)))

        status = self.font.render(f"STATE: {self.state} | MODE: {self.game_mode}", True, WHITE)
        self.screen.blit(status, (SCREEN_WIDTH - 300, 10))
        pygame.display.flip()

    def run(self):
        self.log(f"Server listening on {HOST}:{PORT}")
        
        # Accept clients thread
        def accept_clients():
            while True:
                conn, addr = self.server.accept()
                self.player_counter += 1
                self.players[addr] = {'id': self.player_counter, 'pos': [1,1], 'ready': False, 'ping': 0, 'score': 0}
                self.connections[addr] = conn
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        
        threading.Thread(target=accept_clients, daemon=True).start()

        # Main Server Tick (60 FPS)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.record_replay()
            self.broadcast_state()
            self.draw_spectator()
            self.clock.tick(60)

if __name__ == "__main__":
    server = GameServer()
    server.run()
