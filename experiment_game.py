import math
import random
import time
import tkinter as tk

# ----------------------
# Configuration
# ----------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
LEFT_BG = "#7bc96f"
RIGHT_BG = "#f7f4ec"

RIGHT_PANEL_PADDING = 10

FIRE_INTERVAL_MS = 4000
FIRE_SIZE = 26  # diameter-ish
SCORE_START = 1000
FIRE_SPAWN_SCORE_PENALTY = 10
TIMER_SECONDS = 120

class ExperimentGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Experiment - Fire & Irrigation")
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
            highlightthickness=0,
            cursor="none"
        )
        self.left_canvas.grid(row=1, column=0, sticky="nsew")
        self.left_canvas.bind("<Configure>", self._draw_grass_background)
        self.left_canvas.bind("<Motion>", self.on_left_motion)
        self.left_canvas.bind("<Leave>", self.on_left_leave)
        self.left_canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.left_canvas.bind("<ButtonRelease-1>", self.on_left_release)

        # Right side: dirt field with pipe infrastructure
        self.right_frame = tk.Frame(self.container, bg=RIGHT_BG)
        self.right_frame.grid(row=1, column=1, sticky="nsew")
        self._build_right_scene()

        self.fire_counter = 0
        self.fires_paused = False
        self.game_over = False
        self.active_fires = set()
        self.lake_bounds = (0, 0, 0, 0)
        self.bucket_is_full = False
        self.bucket_is_filling = False
        self.bucket_fill_after_id = None
        self.bucket_fill_anim_after_id = None
        self.bucket_fill_started_at = 0.0
        self.bucket_fill_progress = 0.0
        self.left_mouse_down = False
        self.pointer_x = 0
        self.pointer_y = 0
        self.root.after(500, self.schedule_next_fire)
        self.root.after(1000, self.on_fire_tick)
        self.root.after(1000, self.on_timer_tick)

    def _build_right_scene(self):
        self.valve_total = 4
        self.completed_valves = 0
        self.active_valve_index = None
        self.active_valve_start = 0.0
        self.active_valve_progress = 0.0
        self.valve_hold_after_id = None
        self.valve_hold_ms = 10000
        self.valve_centers = []
        self.valve_radius = 0
        self.sprinkler_on = False

        self.right_canvas = tk.Canvas(
            self.right_frame,
            bg="#7a5634",
            highlightthickness=0
        )
        self.right_canvas.pack(fill="both", expand=True, padx=RIGHT_PANEL_PADDING, pady=RIGHT_PANEL_PADDING)
        self.right_canvas.bind("<Configure>", self._draw_right_scene)
        self.right_canvas.bind("<ButtonPress-1>", self.on_right_press)
        self.right_canvas.bind("<ButtonRelease-1>", self.on_right_release)
        self.right_canvas.bind("<Leave>", self.on_right_leave)

    def _draw_right_scene(self, event=None):
        canvas = self.right_canvas
        if event is not None:
            w = event.width
            h = event.height
        else:
            w = canvas.winfo_width()
            h = canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        canvas.delete("all")

        # Scene layers: sky at top, grass strip, then dirt underground.
        ground_y = max(70, int(h * 0.2))
        grass_h = max(14, int(h * 0.03))
        dirt_top = ground_y + grass_h

        canvas.create_rectangle(0, 0, w, ground_y, fill="#9fd6ff", outline="")
        canvas.create_rectangle(0, ground_y, w, dirt_top, fill="#69b34c", outline="")
        canvas.create_rectangle(0, dirt_top, w, h, fill="#7a5634", outline="")

        # Dirt texture (only below the grass line).
        dirt_h = max(1, h - dirt_top)
        speck_count = max(80, (w * dirt_h) // 9000)
        for i in range(speck_count):
            px = (i * 37 + 19) % max(1, w)
            py = dirt_top + ((i * 53 + 11) % max(1, dirt_h))
            r = 1 + (i % 2)
            color = ("#6a472a", "#8a6440", "#5e3f24")[i % 3]
            canvas.create_oval(px - r, py - r, px + r, py + r, fill=color, outline="")
        crack_count = max(20, w // 25)
        for i in range(crack_count):
            x0 = (i * 29 + 7) % max(1, w)
            y0 = dirt_top + ((i * 47 + 13) % max(1, dirt_h))
            x1 = x0 + ((i * 17) % 52) - 26
            y1 = y0 + 8 + ((i * 11) % 16)
            canvas.create_line(x0, y0, x1, y1, fill="#654427", width=1)

        # Main vertical pipe through the middle.
        pipe_x = w * 0.5
        pipe_w = max(28, int(w * 0.08))
        pipe_top = dirt_top + 10
        pipe_bottom = int(h * 0.82)
        canvas.create_rectangle(
            pipe_x - pipe_w / 2,
            pipe_top,
            pipe_x + pipe_w / 2,
            pipe_bottom,
            fill="#7f8a92",
            outline="#59636a",
            width=3
        )
        canvas.create_line(
            pipe_x - pipe_w * 0.18,
            pipe_top + 6,
            pipe_x - pipe_w * 0.18,
            pipe_bottom - 6,
            fill="#a7b0b6",
            width=2
        )
        canvas.create_line(
            pipe_x + pipe_w * 0.18,
            pipe_top + 6,
            pipe_x + pipe_w * 0.18,
            pipe_bottom - 6,
            fill="#5c666e",
            width=2
        )
        # Above-ground riser up to sprinkler.
        riser_bottom = pipe_top
        riser_top = max(10, ground_y - 22)
        riser_w = pipe_w * 0.42
        canvas.create_rectangle(
            pipe_x - riser_w / 2,
            riser_top,
            pipe_x + riser_w / 2,
            riser_bottom,
            fill="#7f8a92",
            outline="#59636a",
            width=2
        )
        # Grass mound around pipe exit so sprinkler reads as sitting on grass.
        canvas.create_oval(
            pipe_x - pipe_w * 1.1,
            ground_y - grass_h * 0.6,
            pipe_x + pipe_w * 1.1,
            ground_y + grass_h * 0.9,
            fill="#5ba741",
            outline=""
        )

        # Water level rises from reservoir to sprinkler as valves are completed.
        water_fraction = (self.completed_valves + self.active_valve_progress) / float(self.valve_total)
        water_fraction = max(0.0, min(1.0, water_fraction))
        total_column_top = riser_top
        total_column_height = pipe_bottom - total_column_top
        water_top = pipe_bottom - total_column_height * water_fraction
        if water_fraction > 0.0:
            main_top = max(water_top, pipe_top)
            if main_top < pipe_bottom:
                canvas.create_rectangle(
                    pipe_x - pipe_w * 0.26,
                    main_top,
                    pipe_x + pipe_w * 0.26,
                    pipe_bottom,
                    fill="#4ba3d8",
                    outline=""
                )
            if water_top < pipe_top:
                riser_fill_top = max(water_top, riser_top)
                canvas.create_rectangle(
                    pipe_x - riser_w * 0.26,
                    riser_fill_top,
                    pipe_x + riser_w * 0.26,
                    pipe_top,
                    fill="#4ba3d8",
                    outline=""
                )

        # Reservoir at the bottom (underground water body).
        reservoir_top = int(h * 0.8)
        reservoir_bottom = h + int(h * 0.12)
        reservoir_left = int(w * 0.2)
        reservoir_right = int(w * 0.8)
        canvas.create_oval(
            reservoir_left,
            reservoir_top,
            reservoir_right,
            reservoir_bottom,
            fill="#2f78b2",
            outline="#22557d",
            width=3
        )
        canvas.create_oval(
            reservoir_left + 20,
            reservoir_top + 10,
            reservoir_right - 20,
            reservoir_bottom - 16,
            fill="#4f98cd",
            outline=""
        )
        canvas.create_text(
            w * 0.5,
            reservoir_top + 22,
            text="UNDERGROUND RESERVOIR",
            fill="#d7ebfb",
            font=("Georgia", 11, "bold")
        )

        # Four valves at equal distances.
        self.valve_centers = []
        self.valve_radius = max(10, int(pipe_w * 0.32))
        valve_track_top = pipe_top + (pipe_bottom - pipe_top) * 0.16
        valve_track_bottom = pipe_bottom - (pipe_bottom - pipe_top) * 0.08
        valve_spacing = (valve_track_bottom - valve_track_top) / max(1, self.valve_total - 1)
        valve_x = pipe_x + pipe_w * 1.05
        expected_idx = self.completed_valves
        for idx in range(self.valve_total):
            y = valve_track_bottom - idx * valve_spacing
            self.valve_centers.append((valve_x, y))
            canvas.create_line(
                pipe_x - pipe_w * 0.55,
                y,
                pipe_x + pipe_w * 0.55,
                y,
                fill="#5b666d",
                width=5
            )
            if idx < self.completed_valves:
                fill = "#7ec850"
            elif idx == expected_idx and self.active_valve_index == idx:
                fill = "#e5b048"
            elif idx == expected_idx:
                fill = "#d1883b"
            else:
                fill = "#6c757c"
            canvas.create_oval(
                valve_x - self.valve_radius,
                y - self.valve_radius,
                valve_x + self.valve_radius,
                y + self.valve_radius,
                fill=fill,
                outline="#2f3438",
                width=2,
                tags=("valve", f"valve_{idx}")
            )
            canvas.create_text(
                valve_x,
                y,
                text=str(idx + 1),
                fill="#20262b",
                font=("Georgia", 10, "bold"),
                tags=("valve", f"valve_{idx}")
            )

        # Sprinkler at the top.
        head_y = max(8, ground_y - 28)
        arm_len = max(54, int(w * 0.16))
        canvas.create_rectangle(
            pipe_x - pipe_w * 0.65,
            head_y - 10,
            pipe_x + pipe_w * 0.65,
            head_y + 4,
            fill="#6f7b82",
            outline="#4f5960",
            width=2
        )
        canvas.create_line(
            pipe_x - arm_len / 2,
            head_y - 3,
            pipe_x + arm_len / 2,
            head_y - 3,
            fill="#657077",
            width=6,
            capstyle="round"
        )
        for x in (pipe_x - arm_len / 2, pipe_x + arm_len / 2):
            canvas.create_oval(
                x - 8,
                head_y - 11,
                x + 8,
                head_y + 5,
                fill="#59636a",
                outline="#434c53",
                width=2
            )
        if self.sprinkler_on:
            spray_color = "#7cc8f2"
            for side in (-1, 1):
                sx = pipe_x + side * arm_len * 0.45
                for step in range(4):
                    y0 = head_y + 2 + step * 8
                    x_shift = side * (8 + step * 7)
                    canvas.create_line(
                        sx,
                        y0,
                        sx + x_shift,
                        y0 + 14,
                        fill=spray_color,
                        width=2
                    )
            canvas.create_text(
                pipe_x,
                head_y - 34,
                text="SPRINKLER ONLINE",
                fill="#1e2a34",
                font=("Georgia", 11, "bold")
            )
        else:
            canvas.create_line(
                pipe_x - 16,
                head_y - 26,
                pipe_x + 16,
                head_y + 6,
                fill="#b52323",
                width=4
            )
            canvas.create_line(
                pipe_x + 16,
                head_y - 26,
                pipe_x - 16,
                head_y + 6,
                fill="#b52323",
                width=4
            )
            canvas.create_text(
                pipe_x,
                head_y - 34,
                text="SPRINKLER OFFLINE",
                fill="#2c1a12",
                font=("Georgia", 11, "bold")
            )

        # Hold guidance text.
        if not self.sprinkler_on:
            current = min(self.completed_valves + 1, self.valve_total)
            if self.active_valve_index is not None:
                remaining = max(0.0, (self.valve_hold_ms / 1000.0) - (time.monotonic() - self.active_valve_start))
                info = f"Hold valve {current} for {remaining:0.1f}s"
            else:
                info = f"Hold valve {current} for 10.0s"
            canvas.create_text(
                w * 0.5,
                h - 26,
                text=info,
                fill="#2b1d13",
                font=("Georgia", 12, "bold")
            )

    def on_right_press(self, event):
        if self.game_over or self.sprinkler_on:
            return
        valve_index = self._right_valve_index_at(event.x, event.y)
        if valve_index is None or valve_index != self.completed_valves:
            return
        self.active_valve_index = valve_index
        self.active_valve_start = time.monotonic()
        self.active_valve_progress = 0.0
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self._tick_valve_hold()

    def on_right_release(self, event):
        self._cancel_valve_hold()

    def on_right_leave(self, event):
        self._cancel_valve_hold()

    def _tick_valve_hold(self):
        if self.active_valve_index is None or self.sprinkler_on:
            self.valve_hold_after_id = None
            return
        elapsed = time.monotonic() - self.active_valve_start
        self.active_valve_progress = max(0.0, min(1.0, elapsed / (self.valve_hold_ms / 1000.0)))
        if self.active_valve_progress >= 1.0:
            self.completed_valves += 1
            self.active_valve_index = None
            self.active_valve_progress = 0.0
            self.valve_hold_after_id = None
            if self.completed_valves >= self.valve_total:
                self._activate_sprinkler()
            else:
                self._draw_right_scene()
            return
        self._draw_right_scene()
        self.valve_hold_after_id = self.root.after(60, self._tick_valve_hold)

    def _cancel_valve_hold(self):
        if self.active_valve_index is None:
            return
        self.active_valve_index = None
        self.active_valve_progress = 0.0
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self._draw_right_scene()

    def _right_valve_index_at(self, x, y):
        items = self.right_canvas.find_overlapping(x, y, x, y)
        for item_id in reversed(items):
            tags = self.right_canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("valve_"):
                    return int(tag.split("_", 1)[1])
        for idx, (vx, vy) in enumerate(self.valve_centers):
            dx = x - vx
            dy = y - vy
            if dx * dx + dy * dy <= (self.valve_radius + 6) * (self.valve_radius + 6):
                return idx
        return None

    def _activate_sprinkler(self):
        if self.sprinkler_on:
            return
        self.sprinkler_on = True
        self.fires_paused = True
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self.active_valve_index = None
        self.active_valve_progress = 0.0
        for tag in list(self.active_fires):
            self.remove_fire(tag)
        self._draw_right_scene()

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
        for _ in range(20):
            if not self._point_in_lake(x, y):
                break
            x = random.randint(margin, width - margin)
            y = random.randint(margin, height - margin)

        self.fire_counter += 1
        tag = f"fire_{self.fire_counter}"

        self._draw_fire(x, y, size, tag)
        self.active_fires.add(tag)

        self.update_score(-FIRE_SPAWN_SCORE_PENALTY)
        self.schedule_next_fire()

    def on_left_motion(self, event):
        self.pointer_x = event.x
        self.pointer_y = event.y
        self._draw_bucket_cursor(event.x, event.y)
        if self.bucket_is_filling and not self._point_in_lake(event.x, event.y):
            self._cancel_bucket_fill()

    def on_left_leave(self, event):
        self.left_canvas.delete("bucket_cursor")
        if self.bucket_is_filling:
            self._cancel_bucket_fill()

    def on_left_press(self, event):
        if self.game_over:
            return
        self.left_mouse_down = True
        self.pointer_x = event.x
        self.pointer_y = event.y
        self._draw_bucket_cursor(event.x, event.y)

        fire_tag = self._fire_tag_at_point(event.x, event.y)
        if fire_tag is not None:
            if self.bucket_is_full:
                self.remove_fire(fire_tag)
                self.bucket_is_full = False
                self._draw_bucket_cursor(event.x, event.y)
            return

        if self._point_in_lake(event.x, event.y) and not self.bucket_is_full:
            self._start_bucket_fill()

    def on_left_release(self, event):
        self.left_mouse_down = False
        if self.bucket_is_filling:
            self._cancel_bucket_fill()

    def _start_bucket_fill(self):
        if self.bucket_is_filling or self.bucket_is_full:
            return
        self.bucket_is_filling = True
        self.bucket_fill_started_at = time.monotonic()
        self.bucket_fill_progress = 0.0
        self.bucket_fill_after_id = self.root.after(2000, self._finish_bucket_fill)
        self._tick_bucket_fill_animation()

    def _cancel_bucket_fill(self):
        self.bucket_is_filling = False
        if self.bucket_fill_after_id is not None:
            self.root.after_cancel(self.bucket_fill_after_id)
            self.bucket_fill_after_id = None
        if self.bucket_fill_anim_after_id is not None:
            self.root.after_cancel(self.bucket_fill_anim_after_id)
            self.bucket_fill_anim_after_id = None
        self.bucket_fill_progress = 0.0

    def _finish_bucket_fill(self):
        self.bucket_fill_after_id = None
        if self.bucket_fill_anim_after_id is not None:
            self.root.after_cancel(self.bucket_fill_anim_after_id)
            self.bucket_fill_anim_after_id = None
        if self.left_mouse_down and self._point_in_lake(self.pointer_x, self.pointer_y):
            self.bucket_is_full = True
        self.bucket_is_filling = False
        self.bucket_fill_progress = 0.0
        self._draw_bucket_cursor(self.pointer_x, self.pointer_y)

    def _tick_bucket_fill_animation(self):
        if not self.bucket_is_filling:
            self.bucket_fill_anim_after_id = None
            return
        elapsed = time.monotonic() - self.bucket_fill_started_at
        self.bucket_fill_progress = max(0.0, min(1.0, elapsed / 2.0))
        self._draw_bucket_cursor(self.pointer_x, self.pointer_y)
        self.bucket_fill_anim_after_id = self.root.after(80, self._tick_bucket_fill_animation)

    def _fire_tag_at_point(self, x, y):
        items = self.left_canvas.find_overlapping(x, y, x, y)
        for item_id in reversed(items):
            tags = self.left_canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("fire_"):
                    return tag
        return None

    def _point_in_lake(self, x, y):
        x0, y0, x1, y1 = self.lake_bounds
        if x1 <= x0 or y1 <= y0:
            return False
        cx = (x0 + x1) * 0.5
        cy = (y0 + y1) * 0.5
        rx = (x1 - x0) * 0.5
        ry = (y1 - y0) * 0.5
        if rx <= 0 or ry <= 0:
            return False
        dx = (x - cx) / rx
        dy = (y - cy) / ry
        return dx * dx + dy * dy <= 1.0

    def show_end_overlay(self):
        self.end_label.config(text=self._format_score())
        self.end_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.end_overlay.lift()

    def end_game(self):
        if self.game_over:
            return
        self.game_over = True
        self.fires_paused = True
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        if self.bucket_is_filling:
            self._cancel_bucket_fill()
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
        self.left_canvas.delete("lake")
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

        lake_w = max(140, int(width * 0.24))
        lake_h = max(90, int(height * 0.18))
        lake_x0 = int(width * 0.06)
        lake_y0 = int(height * 0.74)
        lake_x1 = min(width - 20, lake_x0 + lake_w)
        lake_y1 = min(height - 10, lake_y0 + lake_h)
        self.lake_bounds = (lake_x0, lake_y0, lake_x1, lake_y1)

        self.left_canvas.create_oval(
            lake_x0,
            lake_y0,
            lake_x1,
            lake_y1,
            fill="#3b82c4",
            outline="#2d5f8f",
            width=2,
            tags="lake"
        )
        self.left_canvas.create_oval(
            lake_x0 + 14,
            lake_y0 + 10,
            lake_x1 - 14,
            lake_y1 - 16,
            fill="#6eb6e8",
            outline="",
            tags="lake"
        )
        self.left_canvas.create_text(
            (lake_x0 + lake_x1) * 0.5,
            (lake_y0 + lake_y1) * 0.5,
            text="LAKE",
            fill="#1f4f78",
            font=("Georgia", 12, "bold"),
            tags="lake"
        )

        self.left_canvas.tag_lower("grass")
        self.left_canvas.tag_raise("lake")
        self.left_canvas.tag_raise("fire")
        self._draw_bucket_cursor(self.pointer_x, self.pointer_y)

    def _draw_bucket_cursor(self, x, y):
        if x <= 0 and y <= 0:
            return
        self.left_canvas.delete("bucket_cursor")
        offset_x = 14
        offset_y = 14
        bx = x + offset_x
        by = y + offset_y

        body_fill = "#58aee2" if self.bucket_is_full else "#b8c2cc"
        if self.bucket_is_filling:
            body_fill = "#7fc4ed"

        self.left_canvas.create_arc(
            bx - 8,
            by - 14,
            bx + 16,
            by + 12,
            start=20,
            extent=140,
            style="arc",
            outline="#555555",
            width=2,
            tags="bucket_cursor"
        )
        self.left_canvas.create_polygon(
            bx - 2,
            by - 2,
            bx + 14,
            by - 2,
            bx + 12,
            by + 14,
            bx,
            by + 14,
            fill=body_fill,
            outline="#555555",
            width=2,
            tags="bucket_cursor"
        )
        if self.bucket_is_filling:
            water_top = by + 12 - int(11 * self.bucket_fill_progress)
            self.left_canvas.create_rectangle(
                bx + 1,
                water_top,
                bx + 11,
                by + 12,
                fill="#8fd8fb",
                outline="",
                tags="bucket_cursor"
            )
            shimmer_x = bx + 2 + int((time.monotonic() * 20) % 7)
            self.left_canvas.create_line(
                shimmer_x,
                water_top + 1,
                shimmer_x + 4,
                water_top + 1,
                fill="#d8f3ff",
                width=1,
                tags="bucket_cursor"
            )
        elif self.bucket_is_full:
            self.left_canvas.create_rectangle(
                bx + 1,
                by + 1,
                bx + 11,
                by + 4,
                fill="#86cff7",
                outline="",
                tags="bucket_cursor"
            )
        self.left_canvas.tag_raise("bucket_cursor")

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
