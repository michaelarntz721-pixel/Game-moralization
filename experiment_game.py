import math
import random
import tkinter as tk
from dataclasses import dataclass

# ----------------------
# Configuration
# ----------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
LEFT_BG = "#7bc96f"
RIGHT_BG = "#f7f4ec"

MAZE_ROWS = 18
MAZE_COLS = 18
MAZE_CELL = 22
MAZE_PADDING = 16
MAZE_DEAD_END_RATIO_MIN = 0.35
MAZE_MAX_REGEN = 25

FIRE_INTERVAL_MS = 4000
FIRE_SIZE = 26  # diameter-ish
SCORE_START = 1000
FIRE_SPAWN_SCORE_PENALTY = 10
TIMER_SECONDS = 120

# ----------------------
# Maze generator
# ----------------------
def generate_maze(rows, cols):
    walls = [[{"N": True, "S": True, "E": True, "W": True} for _ in range(cols)] for _ in range(rows)]
    visited = [[False for _ in range(cols)] for _ in range(rows)]

    def neighbors(r, c):
        dirs = []
        if r > 0:
            dirs.append((r - 1, c, "N", "S"))
        if r < rows - 1:
            dirs.append((r + 1, c, "S", "N"))
        if c > 0:
            dirs.append((r, c - 1, "W", "E"))
        if c < cols - 1:
            dirs.append((r, c + 1, "E", "W"))
        random.shuffle(dirs)
        return dirs

    stack = [(0, 0)]
    visited[0][0] = True

    while stack:
        r, c = stack[-1]
        moved = False
        for nr, nc, dir_out, dir_in in neighbors(r, c):
            if not visited[nr][nc]:
                walls[r][c][dir_out] = False
                walls[nr][nc][dir_in] = False
                visited[nr][nc] = True
                stack.append((nr, nc))
                moved = True
                break
        if not moved:
            stack.pop()

    return walls


def count_dead_ends(walls):
    dead_ends = 0
    rows = len(walls)
    cols = len(walls[0]) if rows else 0
    for r in range(rows):
        for c in range(cols):
            cell = walls[r][c]
            wall_count = int(cell["N"]) + int(cell["S"]) + int(cell["E"]) + int(cell["W"])
            if wall_count >= 3:
                dead_ends += 1
    return dead_ends


@dataclass
class FireSprite:
    tag: str


class ExperimentGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Experiment - Fire & Maze")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=RIGHT_BG)

        self.container = tk.Frame(root, bg=RIGHT_BG)
        self.container.pack(fill="both", expand=True)

        self.container.columnconfigure(0, weight=3)
        self.container.columnconfigure(1, weight=2)
        self.container.rowconfigure(0, weight=0, minsize=70)
        self.container.rowconfigure(1, weight=1)

        # Header: score centered across both sides
        self.score = SCORE_START
        self.header = tk.Frame(self.container, bg=RIGHT_BG, height=70)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header.grid_propagate(False)
        self.score_label = tk.Label(
            self.header,
            text=self._format_score(),
            font=("Georgia", 36, "bold"),
            bg=RIGHT_BG,
            fg="#c1121f"
        )
        self.score_label.place(relx=0.5, rely=0.55, anchor="center")

        self.time_left = TIMER_SECONDS
        self.timer_label = tk.Label(
            self.header,
            text=self._format_time(self.time_left),
            font=("Georgia", 18, "bold"),
            bg=RIGHT_BG,
            fg="#2b2b2b"
        )
        self.timer_label.place(relx=0.98, rely=0.55, anchor="e")

        # End overlay (big score)
        self.end_overlay = tk.Frame(self.root, bg=RIGHT_BG)
        self.end_label = tk.Label(
            self.end_overlay,
            text=self._format_score(),
            font=("Georgia", 160, "bold"),
            bg=RIGHT_BG,
            fg="#c1121f"
        )
        self.end_label.place(relx=0.5, rely=0.5, anchor="center")
        self.end_overlay.place_forget()

        # Left side: blank canvas
        self.left_canvas = tk.Canvas(
            self.container,
            bg=LEFT_BG,
            highlightthickness=0
        )
        self.left_canvas.grid(row=1, column=0, sticky="nsew")
        self.left_canvas.bind("<Configure>", self._draw_grass_background)

        # Right side: maze
        self.right_frame = tk.Frame(self.container, bg=RIGHT_BG)
        self.right_frame.grid(row=1, column=1, sticky="nsew")
        self._build_maze()

        self.fire_counter = 0
        self.fires_paused = False
        self.game_over = False
        self.active_fires = set()
        self.root.after(500, self.schedule_next_fire)
        self.root.after(1000, self.on_fire_tick)
        self.root.after(1000, self.on_timer_tick)

    def _build_maze(self):
        self.maze_walls = None
        target_dead_ends = int(MAZE_ROWS * MAZE_COLS * MAZE_DEAD_END_RATIO_MIN)
        for _ in range(MAZE_MAX_REGEN):
            candidate = generate_maze(MAZE_ROWS, MAZE_COLS)
            if count_dead_ends(candidate) >= target_dead_ends:
                self.maze_walls = candidate
                break
        if self.maze_walls is None:
            self.maze_walls = generate_maze(MAZE_ROWS, MAZE_COLS)

        canvas_width = MAZE_PADDING * 2 + MAZE_COLS * MAZE_CELL
        canvas_height = MAZE_PADDING * 2 + MAZE_ROWS * MAZE_CELL

        self.maze_canvas = tk.Canvas(
            self.right_frame,
            width=canvas_width,
            height=canvas_height,
            bg=RIGHT_BG,
            highlightthickness=0
        )
        self.maze_canvas.pack(padx=10, pady=10)
        self.maze_bounds = (
            MAZE_PADDING,
            MAZE_PADDING,
            MAZE_PADDING + MAZE_COLS * MAZE_CELL,
            MAZE_PADDING + MAZE_ROWS * MAZE_CELL
        )

        wall_color = "#3f3f3f"
        wall_width = 5

        for r in range(MAZE_ROWS):
            for c in range(MAZE_COLS):
                x0 = MAZE_PADDING + c * MAZE_CELL
                y0 = MAZE_PADDING + r * MAZE_CELL
                x1 = x0 + MAZE_CELL
                y1 = y0 + MAZE_CELL
                cell_walls = self.maze_walls[r][c]
                if cell_walls["N"]:
                    self.maze_canvas.create_line(x0, y0, x1, y0, fill=wall_color, width=wall_width, tags="wall")
                if cell_walls["W"]:
                    self.maze_canvas.create_line(x0, y0, x0, y1, fill=wall_color, width=wall_width, tags="wall")
                if r == MAZE_ROWS - 1 and cell_walls["S"]:
                    self.maze_canvas.create_line(x0, y1, x1, y1, fill=wall_color, width=wall_width, tags="wall")
                if c == MAZE_COLS - 1 and cell_walls["E"]:
                    self.maze_canvas.create_line(x1, y0, x1, y1, fill=wall_color, width=wall_width, tags="wall")

        # Start and end markers
        self.start_center = (
            MAZE_PADDING + MAZE_CELL * 0.5,
            MAZE_PADDING + MAZE_CELL * 0.5
        )
        self.start_cell_bounds = (
            MAZE_PADDING,
            MAZE_PADDING,
            MAZE_PADDING + MAZE_CELL,
            MAZE_PADDING + MAZE_CELL
        )
        self.end_center = (
            MAZE_PADDING + (MAZE_COLS - 0.5) * MAZE_CELL,
            MAZE_PADDING + (MAZE_ROWS - 0.5) * MAZE_CELL
        )
        self.marker_radius = MAZE_CELL * 0.28

        self.start_marker = self.maze_canvas.create_oval(
            self.start_center[0] - self.marker_radius,
            self.start_center[1] - self.marker_radius,
            self.start_center[0] + self.marker_radius,
            self.start_center[1] + self.marker_radius,
            fill="#8bc34a",
            outline=""
        )
        # End marker as a small fire icon
        self._draw_fire_on_canvas(
            self.maze_canvas,
            self.end_center[0],
            self.end_center[1],
            MAZE_CELL * 0.6,
            "maze_fire"
        )

        self.maze_dragging = False
        self.path_ids = []
        self.last_path_point = None
        self.wall_hit_streak = 0
        self.wall_hit_threshold = 6
        self.maze_started = False
        self.maze_canvas.bind("<Button-1>", self.on_maze_press)
        self.maze_canvas.bind("<B1-Motion>", self.on_maze_motion)
        self.maze_canvas.bind("<ButtonRelease-1>", self.on_maze_release)

    def schedule_next_fire(self):
        if self.fires_paused:
            return
        self.root.after(FIRE_INTERVAL_MS, self.spawn_fire)

    def spawn_fire(self):
        if self.fires_paused:
            return
        self.left_canvas.update_idletasks()
        width = self.left_canvas.winfo_width()
        height = self.left_canvas.winfo_height()

        size = random.randint(int(FIRE_SIZE * 0.85), int(FIRE_SIZE * 1.25))
        margin = int(size * 1.4)

        if width < margin * 2 or height < margin * 2:
            self.schedule_next_fire()
            return

        x = random.randint(margin, width - margin)
        y = random.randint(margin, height - margin)

        self.fire_counter += 1
        tag = f"fire_{self.fire_counter}"

        self._draw_fire(x, y, size, tag)
        self.active_fires.add(tag)
        sprite = FireSprite(tag=tag)
        self.left_canvas.tag_bind(
            tag,
            "<Button-1>",
            lambda event, t=sprite.tag: self.remove_fire(t)
        )
        self.left_canvas.tag_bind(
            tag,
            "<Enter>",
            lambda event: self.left_canvas.config(cursor="hand2")
        )
        self.left_canvas.tag_bind(
            tag,
            "<Leave>",
            lambda event: self.left_canvas.config(cursor="")
        )

        self.update_score(-FIRE_SPAWN_SCORE_PENALTY)
        self.schedule_next_fire()

    def on_maze_press(self, event):
        if self.game_over:
            return
        if not self.maze_started:
            if self._point_in_circle(event.x, event.y, self.start_center, self.marker_radius) or \
               self._point_in_rect(event.x, event.y, self.start_cell_bounds):
                self.maze_dragging = True
                self._clear_path(reset_started=False)
                self.last_path_point = (event.x, event.y)
                self.wall_hit_streak = 0
                self.maze_started = True
            return

        # Allow resuming from any non-wall point inside the maze
        if self._point_in_rect(event.x, event.y, self.maze_bounds) and not self._hit_wall(event.x, event.y):
            self.maze_dragging = True
            self.last_path_point = (event.x, event.y)
            self.wall_hit_streak = 0

    def on_maze_motion(self, event):
        if not self.maze_dragging or self.game_over:
            return
        if self._hit_wall(event.x, event.y):
            self.wall_hit_streak += 1
            if self.wall_hit_streak >= self.wall_hit_threshold:
                self.maze_dragging = False
                self._clear_path()
            return
        self.wall_hit_streak = 0
        self._add_path_segment(event.x, event.y)
        if self._point_in_circle(event.x, event.y, self.end_center, self.marker_radius):
            self.end_game()

    def on_maze_release(self, event):
        self.maze_dragging = False
        self.wall_hit_streak = 0

    def show_end_overlay(self):
        self.end_label.config(text=self._format_score())
        self.end_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.end_overlay.lift()

    def end_game(self):
        if self.game_over:
            return
        self.game_over = True
        self.fires_paused = True
        self.show_end_overlay()

    def update_score(self, delta):
        self.score += delta
        self.score_label.config(text=self._format_score())
        if self.end_overlay.winfo_ismapped():
            self.end_label.config(text=self._format_score())

    def on_fire_tick(self):
        if not self.fires_paused and self.active_fires:
            self.update_score(-0.5 * len(self.active_fires))
        self.root.after(1000, self.on_fire_tick)

    def on_timer_tick(self):
        if self.game_over:
            return
        self.time_left -= 1
        if self.time_left <= 0:
            self.time_left = 0
            self.timer_label.config(text=self._format_time(self.time_left))
            self.end_game()
            return
        self.timer_label.config(text=self._format_time(self.time_left))
        self.root.after(1000, self.on_timer_tick)

    def _hit_wall(self, x, y):
        items = self.maze_canvas.find_overlapping(x, y, x, y)
        for item in items:
            if "wall" in self.maze_canvas.gettags(item):
                return True
        return False

    def _point_in_circle(self, x, y, center, radius):
        dx = x - center[0]
        dy = y - center[1]
        return dx * dx + dy * dy <= radius * radius

    def _point_in_rect(self, x, y, rect):
        x0, y0, x1, y1 = rect
        return x0 <= x <= x1 and y0 <= y <= y1

    def _add_path_segment(self, x, y):
        if self.last_path_point is None:
            self.last_path_point = (x, y)
            return
        x0, y0 = self.last_path_point
        line_id = self.maze_canvas.create_line(
            x0,
            y0,
            x,
            y,
            fill="#4aa3df",
            width=3,
            capstyle="round"
        )
        self.path_ids.append(line_id)
        self.last_path_point = (x, y)

    def _clear_path(self, reset_started=True):
        for line_id in self.path_ids:
            self.maze_canvas.delete(line_id)
        self.path_ids = []
        self.last_path_point = None
        if reset_started:
            self.maze_started = False

    def _draw_fire(self, x, y, size, tag):
        self._draw_fire_on_canvas(self.left_canvas, x, y, size, tag)

    def _draw_fire_on_canvas(self, canvas, x, y, size, tag):
        log_y = y + size * 0.8

        # Logs (side view campfire)
        self._draw_log(
            x - size * 0.2,
            log_y,
            size * 2.1,
            size * 0.55,
            -18,
            "#8b5a2b",
            "#a56b35",
            tag,
            canvas
        )
        self._draw_log(
            x + size * 0.25,
            log_y + size * 0.08,
            size * 2.1,
            size * 0.55,
            18,
            "#7a4a22",
            "#965826",
            tag,
            canvas
        )

        # Base glow
        canvas.create_oval(
            x - size * 1.2,
            y - size * 1.0,
            x + size * 1.2,
            y + size * 0.8,
            fill="#ffd39a",
            outline="",
            tags=(tag, "fire")
        )

        # Ember bed
        ember_w = size * 1.2
        ember_h = size * 0.35
        canvas.create_oval(
            x - ember_w,
            y + size * 0.35,
            x + ember_w,
            y + size * 0.35 + ember_h,
            fill="#d06b1a",
            outline="",
            tags=(tag, "fire")
        )
        for _ in range(random.randint(4, 7)):
            ex = x + random.uniform(-ember_w * 0.6, ember_w * 0.6)
            ey = y + size * 0.45 + random.uniform(0, ember_h * 0.6)
            er = size * random.uniform(0.03, 0.07)
            canvas.create_oval(
                ex - er,
                ey - er,
                ex + er,
                ey + er,
                fill="#ffb347",
                outline="",
                tags=(tag, "fire")
            )

        # Flames (layered)
        outer_points = self._flame_points(x, y, size * 1.15, jitter=0.14)
        canvas.create_polygon(
            *outer_points,
            fill="#ff6a00",
            outline="",
            smooth=True,
            tags=(tag, "fire")
        )

        mid_points = self._flame_points(x, y + size * 0.08, size * 0.85, jitter=0.12)
        canvas.create_polygon(
            *mid_points,
            fill="#ff9f1a",
            outline="",
            smooth=True,
            tags=(tag, "fire")
        )

        inner_points = self._flame_points(x, y + size * 0.12, size * 0.6, jitter=0.1)
        canvas.create_polygon(
            *inner_points,
            fill="#ffd166",
            outline="",
            smooth=True,
            tags=(tag, "fire")
        )

        core_size = size * 0.18
        canvas.create_oval(
            x - core_size,
            y - core_size * 1.2,
            x + core_size,
            y + core_size * 0.7,
            fill="#fff3b0",
            outline="",
            tags=(tag, "fire")
        )

        # Sparks
        for _ in range(random.randint(2, 4)):
            sx = x + random.uniform(-size * 0.6, size * 0.6)
            sy = y - random.uniform(size * 0.5, size * 1.2)
            r = size * random.uniform(0.05, 0.12)
            canvas.create_oval(
                sx - r,
                sy - r,
                sx + r,
                sy + r,
                fill="#ffe8a3",
                outline="",
                tags=(tag, "fire")
            )

    def _draw_grass_background(self, event):
        width = event.width
        height = event.height
        self.left_canvas.delete("grass")
        self.left_canvas.create_rectangle(
            0,
            0,
            width,
            height,
            fill="#7bc96f",
            outline="",
            tags="grass"
        )
        for y in range(0, height, 6):
            shade = "#6dbb63" if (y // 6) % 2 == 0 else "#76c56a"
            self.left_canvas.create_line(
                0,
                y,
                width,
                y,
                fill=shade,
                tags="grass"
            )
        for y in range(8, height, 18):
            for x in range(6, width, 22):
                blade_h = random.randint(6, 10)
                jitter = random.randint(-2, 2)
                self.left_canvas.create_line(
                    x + jitter,
                    y,
                    x + jitter,
                    y - blade_h,
                    fill="#5fae58",
                    tags="grass"
                )
        for y in range(14, height, 24):
            for x in range(14, width, 28):
                blade_h = random.randint(8, 14)
                jitter = random.randint(-3, 3)
                self.left_canvas.create_line(
                    x + jitter,
                    y,
                    x + jitter - 4,
                    y - blade_h,
                    fill="#63b65d",
                    tags="grass"
                )
        for y in range(10, height, 16):
            for x in range(10, width, 18):
                blade_h = random.randint(5, 9)
                jitter = random.randint(-2, 2)
                self.left_canvas.create_line(
                    x + jitter,
                    y + 2,
                    x + jitter + 3,
                    y - blade_h,
                    fill="#5aa854",
                    tags="grass"
                )
        self.left_canvas.tag_lower("grass")

    def _flame_points(self, x, y, size, jitter):
        base = [
            (0.0, -1.2),
            (0.45, -0.8),
            (0.6, -0.4),
            (0.7, 0.0),
            (0.9, 0.6),
            (0.0, 1.05),
            (-0.9, 0.6),
            (-0.7, 0.0),
            (-0.6, -0.4),
            (-0.45, -0.8),
        ]
        points = []
        for px, py in base:
            jx = px + random.uniform(-jitter, jitter)
            jy = py + random.uniform(-jitter, jitter)
            points.extend([x + jx * size, y + jy * size])
        return points

    def _draw_log(self, x, y, length, thickness, angle_deg, color, highlight, tag, canvas):
        angle = math.radians(angle_deg)
        half_l = length / 2
        half_t = thickness / 2
        corners = [
            (-half_l, -half_t),
            (half_l, -half_t),
            (half_l, half_t),
            (-half_l, half_t),
        ]
        points = []
        for cx, cy in corners:
            rx = cx * math.cos(angle) - cy * math.sin(angle)
            ry = cx * math.sin(angle) + cy * math.cos(angle)
            points.extend([x + rx, y + ry])
        canvas.create_polygon(
            *points,
            fill=color,
            outline="",
            smooth=True,
            tags=(tag, "fire")
        )

        inner_points = []
        inner_scale = 0.6
        for cx, cy in corners:
            cx *= inner_scale
            cy *= inner_scale
            rx = cx * math.cos(angle) - cy * math.sin(angle)
            ry = cx * math.sin(angle) + cy * math.cos(angle)
            inner_points.extend([x + rx, y + ry])
        canvas.create_polygon(
            *inner_points,
            fill=highlight,
            outline="",
            smooth=True,
            tags=(tag, "fire")
        )


    def remove_fire(self, tag):
        self.left_canvas.delete(tag)
        if tag in self.active_fires:
            self.active_fires.remove(tag)

    def _format_score(self):
        return f"{self.score:.1f}"

    def _format_time(self, total_seconds):
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    root = tk.Tk()
    app = ExperimentGame(root)
    root.mainloop()
