import pygame
import socket
import threading
import json
import time
import sys

# --- CLIENT CONFIGURATION ---
HOST = '127.0.0.1'
PORT = 5555

# --- SCREEN & COLORS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
MAZE_COLOR = (40, 44, 52)
PLAYER_COLORS = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]

class MazeClient:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Maze Game - Client")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Networking
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_id = None
        self.ping = 0
        self.connected = False

        # Game State (Synced from server)
        self.state = "CONNECTING"
        self.server_state = {
            "state": "LOBBY",
            "mode": "Normal",
            "maze": None,
            "players": {},
            "replay": None
        }
        
        # Local UI State
        self.ready = False
        self.selected_mode = "Normal"
        self.replay_active = False
        self.replay_start_time = 0

    def connect_to_server(self):
        try:
            self.client.connect((HOST, PORT))
            self.connected = True
            
            # Start network threads
            threading.Thread(target=self.receive_data, daemon=True).start()
            threading.Thread(target=self.ping_loop, daemon=True).start()
        except Exception as e:
            print(f"Connection failed: {e}")
            self.state = "ERROR"

    def send_data(self, data):
        if self.connected:
            try:
                self.client.sendall((json.dumps(data) + "\n").encode())
            except Exception as e:
                print(f"Send error: {e}")
                self.connected = False

    def receive_data(self):
        buffer = ""
        while self.connected:
            try:
                data = self.client.recv(4096).decode()
                if not data: break
                
                buffer += data
                while "\n" in buffer:
                    message_str, buffer = buffer.split("\n", 1)
                    if message_str.strip():
                        msg = json.loads(message_str)
                        self.handle_server_message(msg)
            except Exception as e:
                print(f"Receive error: {e}")
                break
        self.connected = False
        self.state = "DISCONNECTED"

    def handle_server_message(self, msg):
        msg_type = msg.get("type")
        
        if msg_type == "init":
            self.my_id = msg["id"]
            self.state = "LOBBY"
            
        elif msg_type == "pong":
            # Calculate RTT latency
            self.ping = int((time.time() - msg["time"]) * 1000)
            
        elif msg_type == "update":
            self.server_state = msg
            if self.state != "REPLAYING":
                self.state = msg["state"]

    def ping_loop(self):
        """Sends a ping packet every second."""
        while self.connected:
            self.send_data({"type": "ping", "time": time.time(), "latency": self.ping})
            time.sleep(1)

    def draw_maze(self):
        maze = self.server_state.get("maze")
        if not maze: return

        cell_width = SCREEN_WIDTH // len(maze[0])
        cell_height = SCREEN_HEIGHT // len(maze)

        for y, row in enumerate(maze):
            for x, cell in enumerate(row):
                rect = pygame.Rect(x * cell_width, y * cell_height, cell_width, cell_height)
                if cell == 1: pygame.draw.rect(self.screen, MAZE_COLOR, rect)
                elif cell == 2: pygame.draw.rect(self.screen, GREEN, rect)
                elif cell == 3: pygame.draw.rect(self.screen, RED, rect)

    def draw_players(self, player_data, opacity=255):
        maze = self.server_state.get("maze")
        if not maze: return

        cell_width = SCREEN_WIDTH // len(maze[0])
        cell_height = SCREEN_HEIGHT // len(maze)

        for pid_str, player in player_data.items():
            pid = int(pid_str)
            px, py = player['pos']
            base_color = PLAYER_COLORS[(pid - 1) % len(PLAYER_COLORS)]
            
            # Handle opacity for replay mode
            color = base_color if opacity == 255 else (*base_color, opacity)
            
            p_rect = pygame.Rect(px * cell_width, py * cell_height, cell_width, cell_height)
            
            if opacity == 255:
                pygame.draw.circle(self.screen, color, p_rect.center, cell_width//3)
            else:
                # Draw transparent circle via surface
                s = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (cell_width//2, cell_height//2), cell_width//3)
                self.screen.blit(s, p_rect.topleft)

    def draw_night_mode_mask(self, my_player):
        maze = self.server_state.get("maze")
        if not maze or not my_player: return

        cell_width = SCREEN_WIDTH // len(maze[0])
        cell_height = SCREEN_HEIGHT // len(maze)
        px, py = my_player['pos']
        center = (px * cell_width + cell_width//2, py * cell_height + cell_height//2)

        mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 245)) # Deep fog
        # Cutout circle
        pygame.draw.circle(mask, (0, 0, 0, 0), center, cell_width * 3)
        self.screen.blit(mask, (0, 0))

    def draw_lobby(self):
        self.screen.fill(BLACK)
        title = self.font.render(f"Multiplayer Maze - LOBBY (Ping: {self.ping}ms)", True, WHITE)
        self.screen.blit(title, (50, 50))

        # Mode Selection
        modes = ["Normal"]
        for i, m in enumerate(modes):
            color = GREEN if self.selected_mode == m else GRAY
            text = self.font.render(m, True, color)
            self.screen.blit(text, (50, 150 + i * 40))

        # Players List
        players = self.server_state.get("players", {})
        y_offset = 150
        for pid_str, p in players.items():
            pid = int(pid_str)
            is_me = "(You)" if pid == self.my_id else ""
            status = "Ready" if p.get('ready') else "Not Ready"
            color = GREEN if p.get('ready') else RED
            
            p_text = self.font.render(f"Player {pid} {is_me}: {status}", True, color)
            self.screen.blit(p_text, (400, y_offset))
            y_offset += 40

        # Ready Button
        btn_color = GRAY if not self.ready else GREEN
        pygame.draw.rect(self.screen, btn_color, (50, 350, 200, 50))
        btn_text = self.font.render("READY", True, BLACK)
        self.screen.blit(btn_text, (100, 360))

    def run(self):
        self.connect_to_server()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Input Routing based on State
                if self.state == "LOBBY":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        # Click Ready
                        if 50 <= mx <= 250 and 350 <= my <= 400:
                            self.ready = not self.ready
                            self.send_data({"type": "ready", "status": self.ready, "mode": self.selected_mode})
                        # Click Modes
                        for i, m in enumerate(["Normal"]):
                            if 50 <= mx <= 200 and 150 + i*40 <= my <= 180 + i*40:
                                self.selected_mode = m
                                if self.ready: # Update server if already ready
                                    self.send_data({"type": "ready", "status": self.ready, "mode": self.selected_mode})
                
                elif self.state == "PLAYING":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP: self.send_data({"type": "move", "dx": 0, "dy": -1})
                        elif event.key == pygame.K_DOWN: self.send_data({"type": "move", "dx": 0, "dy": 1})
                        elif event.key == pygame.K_LEFT: self.send_data({"type": "move", "dx": -1, "dy": 0})
                        elif event.key == pygame.K_RIGHT: self.send_data({"type": "move", "dx": 1, "dy": 0})

                elif self.state == "GAME_OVER":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                        self.state = "REPLAYING"
                        self.replay_start_time = time.time()

            # --- RENDERING ---
            self.screen.fill(BLACK)

            if self.state == "LOBBY":
                self.draw_lobby()
            
            elif self.state == "COUNTDOWN":
                self.draw_maze()
                self.draw_players(self.server_state.get("players", {}))
                text = self.font.render("GET READY!", True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 - 20))
            
            elif self.state == "PLAYING":
                self.draw_maze()
                players = self.server_state.get("players", {})
                self.draw_players(players)
                
                if self.server_state.get("mode") == "Night":
                    my_p = players.get(str(self.my_id))
                    self.draw_night_mode_mask(my_p)
                
                # UI Overlay
                ui_text = self.small_font.render(f"Ping: {self.ping}ms | Mode: {self.server_state.get('mode')}", True, WHITE)
                self.screen.blit(ui_text, (10, 10))

            elif self.state == "GAME_OVER":
                winner = self.server_state.get("winner")
                self.screen.fill(BLACK)
                text1 = self.font.render(
                    f"PLAYER {winner} WINS!",
                    True,
                    GREEN
                )
                text2 = self.small_font.render(
                    "Press R to watch replay",
                    True,
                    WHITE
                )

                text3 = self.small_font.render(
                    "Press H to return home",
                    True,
                    WHITE
                )

                self.screen.blit(text1, (250, 220))
                self.screen.blit(text2, (250, 280))
                self.screen.blit(text3, (250, 320))

            elif self.state == "REPLAYING":
                replay_data = self.server_state.get("replay", {})
                if not replay_data:
                    self.state = "GAME_OVER"
                else:
                    elapsed = time.time() - self.replay_start_time
                    # Find the closest timestamp in replay data
                    timestamps = sorted([float(k) for k in replay_data.keys()])
                    current_ts = next((ts for ts in timestamps if ts >= elapsed), timestamps[-1])
                    
                    frame_data = replay_data[str(current_ts)]
                    self.draw_maze()
                    converted = {}

                    for pid, pos in frame_data.items():
                        converted[pid] = {
                            "pos": pos
                        }

                    self.draw_players(converted, opacity=128)
                    
                    rp_text = self.font.render("REPLAY MODE", True, RED)
                    self.screen.blit(rp_text, (10, 10))

                    if elapsed > timestamps[-1] + 2: # End replay after 2 secs of finishing
                        self.state = "GAME_OVER"

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    client = MazeClient()
    client.run()