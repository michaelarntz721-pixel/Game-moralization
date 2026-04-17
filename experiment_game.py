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
WATER_LABEL_COLOR = "#d7ebfb"
RIGHT_UI_FONT = "Trebuchet MS"
RIGHT_UI_FONT_ACCENT = "Palatino Linotype"

FIRE_INTERVAL_MIN_MS = 2500
FIRE_INTERVAL_MAX_MS = 4500
FIRE_SIZE = 26  # diameter-ish
SCORE_START = 1000
FIRE_SPAWN_SCORE_PENALTY = 10
TIMER_SECONDS = 120

class ExperimentGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Experiment - Oheň a zavlažování")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=RIGHT_BG)

        self.container = tk.Frame(root, bg=RIGHT_BG)
        self.container.pack(fill="both", expand=True)

        self.container.columnconfigure(0, weight=1, uniform="half")
        self.container.columnconfigure(1, weight=1, uniform="half")
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

        self.start_overlay = tk.Frame(self.root, bg=RIGHT_BG)
        self.start_title_label = tk.Label(
            self.start_overlay,
            text="Experiment pripraven",
            font=("Georgia", 34, "bold"),
            bg=RIGHT_BG,
            fg="#2b2b2b"
        )
        self.start_title_label.place(relx=0.5, rely=0.44, anchor="center")
        self.start_hint_label = tk.Label(
            self.start_overlay,
            text="Stisknete mezernik pro start",
            font=("Georgia", 20),
            bg=RIGHT_BG,
            fg="#5a5a5a"
        )
        self.start_hint_label.place(relx=0.5, rely=0.54, anchor="center")

        # End overlay (big score)
        self.end_overlay = tk.Frame(self.root, bg=RIGHT_BG)
        self.end_label = tk.Label(
            self.end_overlay,
            text=self._format_score(),
            font=("Georgia", 160, "bold"),
            bg=RIGHT_BG,
            fg="#c1121f"
        )
        self.end_label.place(relx=0.5, rely=0.44, anchor="center")
        self.end_message_label = tk.Label(
            self.end_overlay,
            text="",
            font=("Georgia", 22, "bold"),
            bg=RIGHT_BG,
            fg="#4f3c2f",
            wraplength=900,
            justify="center"
        )
        self.end_message_label.place(relx=0.5, rely=0.66, anchor="center")
        self.end_overlay.place_forget()
        self.countdown_label = tk.Label(
            self.root,
            text="",
            font=("Georgia", 140, "bold"),
            bg=RIGHT_BG,
            fg="#000000"
        )
        self.countdown_label.place_forget()

        # Left side: blank canvas
        self.left_canvas = tk.Canvas(
            self.container,
            bg=LEFT_BG,
            highlightthickness=0,
            cursor="none"
        )
        self.left_canvas.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=RIGHT_PANEL_PADDING,
            pady=RIGHT_PANEL_PADDING
        )
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
        self.fire_positions = {}
        self.lake_bounds = (0, 0, 0, 0)
        self.left_sprinkler_center = (0, 0)
        self.left_sprinkler_clear_radius = 42
        self.bucket_is_full = False
        self.bucket_is_filling = False
        self.bucket_fill_after_id = None
        self.bucket_fill_anim_after_id = None
        self.bucket_pour_after_id = None
        self.bucket_pour_state = None
        self.bucket_fill_started_at = 0.0
        self.bucket_fill_progress = 0.0
        self.left_mouse_down = False
        self.pointer_x = 0
        self.pointer_y = 0
        self.sprinkler_anim_after_id = None
        self.sprinkler_animating = False
        self.sprinkler_anim_end_at = 0.0
        self.sprinkler_next_extinguish_at = 0.0
        self.sprinkler_pending_fires = []
        self.finish_overlay_after_sprinkler = False
        self.countdown_running = False
        self.countdown_value = 0
        self.countdown_after_id = None
        self.game_started = False
        self.root.bind_all("<KeyPress-space>", self.on_space_press)
        self.start_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.start_overlay.lift()
        self.root.after(100, self.root.focus_force)

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

        level_spacing = (pipe_bottom - riser_top) / float(self.valve_total)
        valve_ys = [pipe_bottom - (level_spacing * (idx + 1)) for idx in range(self.valve_total)]

        # Water level rises to the actual height of each valve line.
        if self.sprinkler_on:
            water_top = riser_top
        else:
            water_stages = [pipe_bottom] + valve_ys
            stage_index = min(self.completed_valves, self.valve_total - 1)
            start_top = water_stages[stage_index]
            end_top = water_stages[stage_index + 1]
            progress = self.active_valve_progress if self.active_valve_index is not None else 0.0
            water_top = start_top + ((end_top - start_top) * progress)
        if water_top < pipe_bottom:
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
        reservoir_top = pipe_bottom
        reservoir_bottom = h + int(h * 0.12)
        reservoir_left = int(w * 0.24)
        reservoir_right = int(w * 0.76)
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
            reservoir_top + (reservoir_bottom - reservoir_top) * 0.42,
            text="PODZEMNÍ NÁDRŽ",
            fill=WATER_LABEL_COLOR,
            font=(RIGHT_UI_FONT, 11, "bold")
        )

        # Four equal milestones in the pipe, with the control valves grouped
        # together so the player reads the task as "one valve = one level".
        self.valve_centers = []
        level_badge_radius = max(13, int(min(w, h) * 0.018))
        expected_idx = self.completed_valves
        for idx in range(self.valve_total):
            y = valve_ys[idx]
            is_completed = idx < self.completed_valves
            is_active = idx == expected_idx and self.active_valve_index == idx
            is_next = idx == expected_idx and self.active_valve_index is None
            if is_completed:
                line_color = "#5bc16d"
                badge_fill = "#7ec850"
            elif is_active:
                line_color = "#f0c65a"
                badge_fill = "#e5b048"
            elif is_next:
                line_color = "#d49a45"
                badge_fill = "#d1883b"
            else:
                line_color = "#7b858c"
                badge_fill = "#6c757c"
            guide_half_width = pipe_w * 0.7 if y >= pipe_top else riser_w * 1.6
            canvas.create_line(
                pipe_x - guide_half_width,
                y,
                pipe_x + guide_half_width,
                y,
                fill=line_color,
                width=6 if (is_active or is_next) else 4
            )
            badge_x = pipe_x - guide_half_width - level_badge_radius - 24
            canvas.create_oval(
                badge_x - level_badge_radius,
                y - level_badge_radius,
                badge_x + level_badge_radius,
                y + level_badge_radius,
                fill=badge_fill,
                outline="#2f3438",
                width=2
            )
            canvas.create_text(
                badge_x,
                y,
                text=str(idx + 1),
                fill="#20262b",
                font=(RIGHT_UI_FONT, 12, "bold")
            )

        panel_left = int(max(pipe_x + pipe_w * 1.7, w * 0.56))
        panel_right = w - 18
        panel_bottom = int(min(h - 18, reservoir_top - 10))
        panel_top = max(dirt_top + 24, panel_bottom - 230)
        panel_center_x = (panel_left + panel_right) * 0.5
        canvas.create_rectangle(
            panel_left,
            panel_top,
            panel_right,
            panel_bottom,
            fill="#8b623d",
            outline="#5d4028",
            width=3
        )
        canvas.create_text(
            panel_center_x,
            panel_top + 18,
            text="OTOČTE VENTILY 1 AŽ 4",
            fill="#f7f1e3",
            font=(RIGHT_UI_FONT_ACCENT, 13, "bold")
        )
        canvas.create_text(
            panel_center_x,
            panel_top + 36,
            text="Každý ventil zvedne vodu o jednu úroveň.",
            fill="#f2dfc2",
            font=(RIGHT_UI_FONT, 10, "normal")
        )
        valve_center_x = panel_left + 36
        valve_stack_top = panel_top + 70
        valve_stack_bottom = panel_bottom - 24
        valve_spacing = (valve_stack_bottom - valve_stack_top) / max(1, self.valve_total - 1)
        base_valve_radius = max(9, int(min(w, h) * 0.016))
        spacing_limited_radius = max(9, int(valve_spacing * 0.34))
        self.valve_radius = min(base_valve_radius, spacing_limited_radius)
        for idx in range(self.valve_total):
            vx = valve_center_x
            vy = valve_stack_bottom - idx * valve_spacing
            self.valve_centers.append((vx, vy))
            is_completed = idx < self.completed_valves
            is_active = idx == expected_idx and self.active_valve_index == idx
            is_next = idx == expected_idx and self.active_valve_index is None
            if is_completed:
                fill = "#7ec850"
                label = "HOTOVO"
                label_color = "#d9ffd1"
            elif is_active:
                fill = "#e5b048"
                label = "DRŽET"
                label_color = "#fff0b8"
            elif is_next:
                fill = "#d1883b"
                label = "DALŠÍ"
                label_color = "#ffe1b3"
            else:
                fill = "#6c757c"
                label = "ZAMČENO"
                label_color = "#d5d9dc"
            if idx < self.valve_total - 1:
                next_vy = valve_stack_bottom - (idx + 1) * valve_spacing
                canvas.create_line(
                    vx,
                    next_vy + self.valve_radius + 6,
                    vx,
                    vy - self.valve_radius - 6,
                    fill="#6a472a",
                    width=4
                )
            canvas.create_oval(
                vx - self.valve_radius,
                vy - self.valve_radius,
                vx + self.valve_radius,
                vy + self.valve_radius,
                fill=fill,
                outline="#2f3438",
                width=2,
                tags=("valve", f"valve_{idx}")
            )
            canvas.create_text(
                vx,
                vy,
                text=str(idx + 1),
                fill="#20262b",
                font=(RIGHT_UI_FONT, 11, "bold"),
                tags=("valve", f"valve_{idx}")
            )
            spin_angle = 0.0
            if is_active:
                spin_angle = (time.monotonic() * 40.0) % 360.0
            self._draw_valve_wheel(
                canvas,
                vx,
                vy,
                self.valve_radius + 4,
                spin_angle,
                is_active,
                idx
            )
            canvas.create_text(
                vx + self.valve_radius + 16,
                vy - 8,
                text=f"VENTIL {idx + 1}",
                anchor="w",
                fill="#f7f1e3",
                font=(RIGHT_UI_FONT, 11, "bold")
            )
            canvas.create_text(
                vx + self.valve_radius + 16,
                vy + 10,
                text=label,
                anchor="w",
                fill=label_color,
                font=(RIGHT_UI_FONT, 10, "bold")
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
                text="ZAVLAŽOVACÍ SYSTÉM AKTIVNÍ",
                fill="#1e2a34",
                font=(RIGHT_UI_FONT_ACCENT, 12, "bold")
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
                text="ŽÁDNÝ TLAK",
                fill="#2c1a12",
                font=(RIGHT_UI_FONT_ACCENT, 12, "bold")
            )

        profile_left = 22
        profile_right = w - 22
        if self.fire_positions:
            canvas.create_text(
                (profile_left + profile_right) * 0.5,
                ground_y - 30,
                fill="#5a2d16",
                font=(RIGHT_UI_FONT, 10, "bold")
            )
            left_width = max(1, self.left_canvas.winfo_width())
            left_height = max(1, self.left_canvas.winfo_height())
            surface_top = max(ground_y - 12, 8)
            surface_bottom = dirt_top - 8
            for tag, (fx, fy, _) in sorted(self.fire_positions.items(), key=lambda item: item[1][0]):
                rel_x = max(0.0, min(1.0, fx / float(left_width)))
                rel_y = max(0.0, min(1.0, fy / float(left_height)))
                profile_x = profile_left + ((profile_right - profile_left) * rel_x)
                profile_y = surface_top + ((surface_bottom - surface_top) * rel_y)
                self._draw_fire_on_canvas(
                    canvas,
                    profile_x,
                    profile_y,
                    8,
                    f"profile_{tag}"
                )

        self._refresh_countdown_overlay()

    def on_right_press(self, event):
        if not self.game_started or self.game_over or self.sprinkler_on:
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
        self.game_over = True
        self.fires_paused = True
        self.finish_overlay_after_sprinkler = True
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self.active_valve_index = None
        self.active_valve_progress = 0.0
        self._draw_right_scene()
        self.finish_overlay_after_sprinkler = True
        self._start_sprinkler_extinguish_animation()

    def _start_sprinkler_extinguish_animation(self):
        if self.sprinkler_anim_after_id is not None:
            self.root.after_cancel(self.sprinkler_anim_after_id)
            self.sprinkler_anim_after_id = None
        self.sprinkler_pending_fires = list(self.active_fires)
        random.shuffle(self.sprinkler_pending_fires)
        self.sprinkler_animating = True
        now = time.monotonic()
        self.sprinkler_anim_end_at = now + 3.0
        self.sprinkler_next_extinguish_at = now + 0.2
        self._tick_sprinkler_extinguish_animation()

    def _tick_sprinkler_extinguish_animation(self):
        if not self.sprinkler_animating:
            self.sprinkler_anim_after_id = None
            return

        self.left_canvas.delete("sprinkler_rain")
        width = max(1, self.left_canvas.winfo_width())
        height = max(1, self.left_canvas.winfo_height())
        sprinkler_x, sprinkler_y = self.left_sprinkler_center
        if sprinkler_x <= 0 and sprinkler_y <= 0:
            sprinkler_x = width * 0.5
            sprinkler_y = height * 0.5
        drop_count = max(18, width // 22)
        for _ in range(drop_count):
            side = random.choice((-1, 1))
            end_x = sprinkler_x + side * random.randint(45, max(46, int(width * 0.34)))
            end_y = sprinkler_y - random.randint(20, max(21, int(height * 0.26)))
            mid_x = (sprinkler_x + end_x) * 0.5 + side * random.randint(6, 18)
            mid_y = min(sprinkler_y, end_y) - random.randint(2, 18)
            self.left_canvas.create_line(
                sprinkler_x,
                sprinkler_y,
                mid_x,
                mid_y,
                end_x,
                end_y,
                fill="#8ed5ff",
                width=2,
                smooth=True,
                tags="sprinkler_rain"
            )
            drip_x = end_x + random.randint(-8, 8)
            drip_y0 = end_y + random.randint(0, 10)
            drip_y1 = drip_y0 + random.randint(8, 18)
            self.left_canvas.create_line(
                drip_x,
                drip_y0,
                drip_x - random.randint(0, 2),
                drip_y1,
                fill="#bcecff",
                width=2,
                tags="sprinkler_rain"
            )
        self.left_canvas.tag_raise("sprinkler_rain")
        self.left_canvas.tag_raise("bucket_cursor")

        now = time.monotonic()
        if now >= self.sprinkler_next_extinguish_at and self.sprinkler_pending_fires:
            tag = self.sprinkler_pending_fires.pop(0)
            center = self._fire_center(tag)
            if center is not None:
                self._draw_splash(center[0], center[1])
            self.remove_fire(tag)
            self.sprinkler_next_extinguish_at = now + 0.2

        if now >= self.sprinkler_anim_end_at and not self.active_fires:
            self.left_canvas.delete("sprinkler_rain")
            self.left_canvas.delete("sprinkler_splash")
            self.sprinkler_animating = False
            self.sprinkler_anim_after_id = None
            if self.finish_overlay_after_sprinkler:
                self.finish_overlay_after_sprinkler = False
                self.show_end_overlay()
            return

        self.sprinkler_anim_after_id = self.root.after(90, self._tick_sprinkler_extinguish_animation)

    def schedule_next_fire(self):
        if self.fires_paused:
            return
        delay_ms = int(random.uniform(FIRE_INTERVAL_MIN_MS, FIRE_INTERVAL_MAX_MS))
        self.root.after(delay_ms, self.spawn_fire)

    def spawn_fire(self):
        if not self.game_started or self.fires_paused:
            return
        self.left_canvas.update_idletasks()
        width = self.left_canvas.winfo_width()
        height = self.left_canvas.winfo_height()

        size = FIRE_SIZE
        margin = int(size * 1.4)

        if width < margin * 2 or height < margin * 2:
            self.schedule_next_fire()
            return

        x = None
        y = None
        for _ in range(60):
            candidate_x = random.randint(margin, width - margin)
            candidate_y = random.randint(margin, height - margin)
            if self._can_place_fire(candidate_x, candidate_y, size):
                x = candidate_x
                y = candidate_y
                break
        if x is None or y is None:
            x = random.randint(margin, width - margin)
            y = random.randint(margin, height - margin)
            self.schedule_next_fire()
            return

        self.fire_counter += 1
        tag = f"fire_{self.fire_counter}"

        self._draw_fire(x, y, size, tag)
        self.active_fires.add(tag)
        self.fire_positions[tag] = (x, y, size)

        self.update_score(-FIRE_SPAWN_SCORE_PENALTY)
        self._draw_right_scene()
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
        if not self.game_started or self.game_over:
            return
        self.left_mouse_down = True
        self.pointer_x = event.x
        self.pointer_y = event.y
        self._draw_bucket_cursor(event.x, event.y)

        fire_tag = self._fire_tag_at_point(event.x, event.y)
        if fire_tag is not None:
            if self.bucket_is_full:
                center = self._fire_center(fire_tag)
                if center is None:
                    self.remove_fire(fire_tag)
                else:
                    self._start_bucket_pour_animation(event.x, event.y, center[0], center[1], fire_tag)
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
        bucket_x0, bucket_y0, bucket_x1, bucket_y1 = self._bucket_cursor_bounds(x, y)
        closest_tag = None
        closest_distance_sq = None
        for tag, (fx, fy, size) in self.fire_positions.items():
            fire_bbox = self.left_canvas.bbox(tag)
            if fire_bbox is not None:
                fire_x0, fire_y0, fire_x1, fire_y1 = fire_bbox
                fire_x0 -= 4
                fire_y0 -= 4
                fire_x1 += 4
                fire_y1 += 4
                if not (
                    bucket_x1 < fire_x0
                    or bucket_x0 > fire_x1
                    or bucket_y1 < fire_y0
                    or bucket_y0 > fire_y1
                ):
                    dx = x - fx
                    dy = y - fy
                    distance_sq = (dx * dx) + (dy * dy)
                    if closest_distance_sq is None or distance_sq < closest_distance_sq:
                        closest_tag = tag
                        closest_distance_sq = distance_sq
                    continue
            radius = self._fire_hit_radius(size)
            dx = x - fx
            dy = y - fy
            distance_sq = (dx * dx) + (dy * dy)
            if distance_sq <= radius * radius:
                if closest_distance_sq is None or distance_sq < closest_distance_sq:
                    closest_tag = tag
                    closest_distance_sq = distance_sq
        if closest_tag is not None:
            return closest_tag
        return None

    def _bucket_cursor_bounds(self, x, y):
        offset_x = 12
        offset_y = 12
        bx = x + offset_x
        by = y + offset_y
        return (
            bx - 11,
            by - 16,
            bx + 11,
            by + 16,
        )

    def _fire_hit_radius(self, size):
        return max(30.0, size * 1.7)

    def _fire_spacing_radius(self, size):
        return max(30.0, size * 1.4)

    def _can_place_fire(self, x, y, size):
        if self._point_in_lake_buffered(x, y, self._fire_lake_buffer(size)) or self._point_in_left_sprinkler_zone(x, y):
            return False
        candidate_radius = self._fire_spacing_radius(size)
        for fx, fy, existing_size in self.fire_positions.values():
            existing_radius = self._fire_spacing_radius(existing_size)
            dx = x - fx
            dy = y - fy
            min_distance = candidate_radius + existing_radius
            if (dx * dx) + (dy * dy) < min_distance * min_distance:
                return False
        return True

    def _fire_lake_buffer(self, size):
        return max(24.0, size * 1.35)

    def _fire_center(self, tag):
        bbox = self.left_canvas.bbox(tag)
        if bbox is None:
            return None
        x0, y0, x1, y1 = bbox
        return ((x0 + x1) * 0.5, (y0 + y1) * 0.5)

    def _start_bucket_pour_animation(self, source_x, source_y, target_x, target_y, fire_tag):
        if self.bucket_pour_after_id is not None:
            self.root.after_cancel(self.bucket_pour_after_id)
            self.bucket_pour_after_id = None
        self.left_canvas.delete("bucket_pour")
        self.bucket_pour_state = {
            "step": 0,
            "steps": 6,
            "sx": source_x,
            "sy": source_y,
            "tx": target_x,
            "ty": target_y,
            "fire_tag": fire_tag,
        }
        self._tick_bucket_pour_animation()

    def _draw_splash(self, x, y):
        splash_tag = f"splash_{random.randint(10000, 99999)}"
        self.left_canvas.create_oval(
            x - 14,
            y - 9,
            x + 14,
            y + 11,
            fill="#8fd8fb",
            outline="",
            tags=(splash_tag, "sprinkler_splash")
        )
        for _ in range(5):
            dx = random.randint(-16, 16)
            dy = random.randint(-16, -4)
            self.left_canvas.create_oval(
                x + dx - 3,
                y + dy - 3,
                x + dx + 3,
                y + dy + 3,
                fill="#bcecff",
                outline="",
                tags=(splash_tag, "sprinkler_splash")
            )
        self.left_canvas.tag_raise("sprinkler_splash")
        self.left_canvas.tag_raise("bucket_cursor")
        self.root.after(220, lambda t=splash_tag: self.left_canvas.delete(t))

    def _tick_bucket_pour_animation(self):
        state = self.bucket_pour_state
        if state is None:
            self.bucket_pour_after_id = None
            return

        step = state["step"]
        steps = state["steps"]
        sx = state["sx"]
        sy = state["sy"]
        tx = state["tx"]
        ty = state["ty"]
        fire_tag = state["fire_tag"]

        direction = 1 if tx >= sx else -1
        mouth_x = sx + direction * 12
        mouth_y = sy + 8
        mid_x = (mouth_x + tx) * 0.5 + direction * 10
        mid_y = (mouth_y + ty) * 0.5 - 8

        self.left_canvas.delete("bucket_pour")
        self.left_canvas.create_line(
            mouth_x,
            mouth_y,
            mid_x,
            mid_y,
            tx,
            ty,
            fill="#86cff7",
            width=2,
            smooth=True,
            tags="bucket_pour"
        )
        for i in range(6):
            u = i / 5.0
            px = ((1 - u) * (1 - u) * mouth_x) + (2 * (1 - u) * u * mid_x) + (u * u * tx)
            py = ((1 - u) * (1 - u) * mouth_y) + (2 * (1 - u) * u * mid_y) + (u * u * ty)
            self.left_canvas.create_oval(
                px - 1.8,
                py - 1.8,
                px + 1.8,
                py + 1.8,
                fill="#a9e1ff",
                outline="",
                tags="bucket_pour"
            )
        self.left_canvas.tag_raise("bucket_pour")
        self.left_canvas.tag_raise("bucket_cursor")

        if step >= steps - 1:
            self.remove_fire(fire_tag)
            self.bucket_pour_state = None
            self.bucket_pour_after_id = self.root.after(90, lambda: self.left_canvas.delete("bucket_pour"))
            return

        state["step"] += 1
        self.bucket_pour_after_id = self.root.after(45, self._tick_bucket_pour_animation)

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

    def _point_in_lake_buffered(self, x, y, padding):
        x0, y0, x1, y1 = self.lake_bounds
        if x1 <= x0 or y1 <= y0:
            return False
        cx = (x0 + x1) * 0.5
        cy = (y0 + y1) * 0.5
        rx = ((x1 - x0) * 0.5) + padding
        ry = ((y1 - y0) * 0.5) + padding
        if rx <= 0 or ry <= 0:
            return False
        dx = (x - cx) / rx
        dy = (y - cy) / ry
        return dx * dx + dy * dy <= 1.0

    def _point_in_left_sprinkler_zone(self, x, y):
        sx, sy = self.left_sprinkler_center
        if sx <= 0 and sy <= 0:
            return False
        dx = x - sx
        dy = y - sy
        return dx * dx + dy * dy <= self.left_sprinkler_clear_radius * self.left_sprinkler_clear_radius

    def show_end_overlay(self):
        self.end_label.config(text=self._format_score())
        if self.score <= 0:
            self.end_message_label.config(
                text="V tomto kole se Vám nepodařilo uchránit žádné peníze."
            )
        else:
            self.end_message_label.config(text="")
        self.end_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.end_overlay.lift()

    def on_space_press(self, event=None):
        if self.game_started or self.game_over or self.countdown_running:
            return
        self.start_overlay.place_forget()
        self._start_countdown()

    def _start_countdown(self):
        self.countdown_running = True
        self._countdown_step(3)

    def _countdown_step(self, value):
        self.countdown_value = value
        self._refresh_countdown_overlay()
        if value <= 1:
            self.countdown_after_id = self.root.after(1000, self._begin_gameplay)
        else:
            self.countdown_after_id = self.root.after(1000, lambda: self._countdown_step(value - 1))

    def _begin_gameplay(self):
        self.countdown_running = False
        self.countdown_value = 0
        self.countdown_after_id = None
        self._refresh_countdown_overlay()
        self.game_started = True
        self.root.after(500, self.schedule_next_fire)
        self.root.after(1000, self.on_fire_tick)
        self.root.after(1000, self.on_timer_tick)

    def _refresh_countdown_overlay(self):
        if not hasattr(self, "countdown_label"):
            return
        if not self.countdown_running or self.countdown_value <= 0:
            self.countdown_label.place_forget()
            return
        self.countdown_label.config(text=str(self.countdown_value))
        self.countdown_label.place(relx=0.5, rely=0.55, anchor="center")
        self.countdown_label.lift()

    def end_game(self):
        if self.game_over:
            return
        self.game_over = True
        if self.countdown_after_id is not None:
            self.root.after_cancel(self.countdown_after_id)
            self.countdown_after_id = None
        self.countdown_running = False
        self.countdown_value = 0
        self._refresh_countdown_overlay()
        self.fires_paused = True
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        if self.bucket_is_filling:
            self._cancel_bucket_fill()
        if self.bucket_pour_after_id is not None:
            self.root.after_cancel(self.bucket_pour_after_id)
            self.bucket_pour_after_id = None
        self.bucket_pour_state = None
        self.left_canvas.delete("bucket_pour")
        if self.sprinkler_anim_after_id is not None:
            self.root.after_cancel(self.sprinkler_anim_after_id)
            self.sprinkler_anim_after_id = None
        self.sprinkler_animating = False
        self.left_canvas.delete("sprinkler_rain")
        self.left_canvas.delete("sprinkler_splash")
        self.show_end_overlay()

    def update_score(self, delta):
        self.score = max(0, self.score + delta)
        self.score_label.config(text=self._format_score())
        if self.end_overlay.winfo_ismapped():
            self.end_label.config(text=self._format_score())
            if self.score <= 0:
                self.end_message_label.config(
                    text="V tomto kole se Vám nepodařilo uchránit žádné peníze."
                )
            else:
                self.end_message_label.config(text="")
        if self.score <= 0 and not self.game_over:
            self.end_game()

    def on_fire_tick(self):
        if not self.game_started or self.game_over:
            return
        if not self.fires_paused and self.active_fires:
            self.update_score(-1 * len(self.active_fires))
        self.root.after(1000, self.on_fire_tick)

    def on_timer_tick(self):
        if not self.game_started or self.game_over:
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
        self.left_canvas.delete("left_sprinkler")
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
        # Extra grass tufts for a more natural field texture.
        for y in range(12, height, 20):
            for x in range(8, width, 16):
                base_x = x + random.randint(-2, 2)
                base_y = y + random.randint(-2, 2)
                h1 = random.randint(8, 14)
                h2 = random.randint(10, 16)
                h3 = random.randint(7, 13)
                self.left_canvas.create_line(
                    base_x,
                    base_y,
                    base_x - 3,
                    base_y - h1,
                    fill="#4e9b48",
                    width=2,
                    tags="grass"
                )
                self.left_canvas.create_line(
                    base_x,
                    base_y,
                    base_x + 1,
                    base_y - h2,
                    fill="#5aa854",
                    width=2,
                    tags="grass"
                )
                self.left_canvas.create_line(
                    base_x,
                    base_y,
                    base_x + 4,
                    base_y - h3,
                    fill="#66b95e",
                    width=2,
                    tags="grass"
                )
        for y in range(20, height, 28):
            for x in range(14, width, 24):
                bend = random.randint(-2, 2)
                h = random.randint(9, 15)
                self.left_canvas.create_line(
                    x,
                    y,
                    x + bend,
                    y - h * 0.55,
                    x + bend + random.randint(-2, 2),
                    y - h,
                    fill="#5fae58",
                    smooth=True,
                    width=2,
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
            text="JEZERO",
            fill=WATER_LABEL_COLOR,
            font=("Georgia", 12, "bold"),
            tags="lake"
        )

        sprinkler_x = int(width * 0.5)
        sprinkler_y = int(height * 0.5)
        self.left_sprinkler_center = (sprinkler_x, sprinkler_y)
        self.left_canvas.create_rectangle(
            sprinkler_x - 4,
            sprinkler_y + 8,
            sprinkler_x + 4,
            sprinkler_y + 36,
            fill="#6f7b82",
            outline="#4f5960",
            width=1,
            tags="left_sprinkler"
        )
        self.left_canvas.create_oval(
            sprinkler_x - 12,
            sprinkler_y - 4,
            sprinkler_x + 12,
            sprinkler_y + 8,
            fill="#7f8a92",
            outline="#4f5960",
            width=2,
            tags="left_sprinkler"
        )
        self.left_canvas.create_line(
            sprinkler_x - 16,
            sprinkler_y + 2,
            sprinkler_x + 16,
            sprinkler_y + 2,
            fill="#657077",
            width=4,
            capstyle="round",
            tags="left_sprinkler"
        )
        for nozzle_x in (sprinkler_x - 16, sprinkler_x + 16):
            self.left_canvas.create_oval(
                nozzle_x - 4,
                sprinkler_y - 2,
                nozzle_x + 4,
                sprinkler_y + 6,
                fill="#59636a",
                outline="#434c53",
                width=1,
                tags="left_sprinkler"
            )

        self.left_canvas.tag_lower("grass")
        self.left_canvas.tag_raise("lake")
        self.left_canvas.tag_raise("left_sprinkler")
        self.left_canvas.tag_raise("fire")
        self._draw_bucket_cursor(self.pointer_x, self.pointer_y)
        self._refresh_countdown_overlay()

    def _draw_bucket_cursor(self, x, y):
        if x <= 0 and y <= 0:
            return
        self.left_canvas.delete("bucket_cursor")
        offset_x = 12
        offset_y = 12
        bx = x + offset_x
        by = y + offset_y

        body_fill = "#58aee2" if self.bucket_is_full else "#b8c2cc"
        if self.bucket_is_filling:
            body_fill = "#96d8ff"

        rim_y = by - 2
        top_w = 16
        bottom_w = 11
        body_h = 16
        left_lug_x = bx - (top_w * 0.5) + 1.6
        right_lug_x = bx + (top_w * 0.5) - 1.6
        lug_y = rim_y + 0.8
        lug_r = 2.1

        # Handle connected directly to the side lugs.
        self.left_canvas.create_line(
            left_lug_x,
            lug_y,
            bx,
            rim_y - 12,
            right_lug_x,
            lug_y,
            fill="#555555",
            width=2,
            smooth=True,
            tags="bucket_cursor"
        )
        self.left_canvas.create_oval(
            left_lug_x - lug_r,
            lug_y - lug_r,
            left_lug_x + lug_r,
            lug_y + lug_r,
            fill="#8e98a2",
            outline="#555555",
            width=1,
            tags="bucket_cursor"
        )
        self.left_canvas.create_oval(
            right_lug_x - lug_r,
            lug_y - lug_r,
            right_lug_x + lug_r,
            lug_y + lug_r,
            fill="#8e98a2",
            outline="#555555",
            width=1,
            tags="bucket_cursor"
        )

        # Rim and body.
        self.left_canvas.create_line(
            bx - top_w * 0.5,
            rim_y,
            bx + top_w * 0.5,
            rim_y,
            fill="#2e5870" if self.bucket_is_filling else "#555555",
            width=3 if self.bucket_is_filling else 2,
            tags="bucket_cursor"
        )
        self.left_canvas.create_polygon(
            bx - top_w * 0.5,
            rim_y,
            bx + top_w * 0.5,
            rim_y,
            bx + bottom_w * 0.5,
            rim_y + body_h,
            bx - bottom_w * 0.5,
            rim_y + body_h,
            fill=body_fill,
            outline="#2e5870" if self.bucket_is_filling else "#555555",
            width=3 if self.bucket_is_filling else 2,
            tags="bucket_cursor"
        )
        if self.bucket_is_filling:
            fill_height = int((body_h - 2) * self.bucket_fill_progress)
            water_top = rim_y + body_h - 1 - fill_height
            self.left_canvas.create_rectangle(
                bx - 5.5,
                water_top,
                bx + 5.5,
                rim_y + body_h - 1,
                fill="#57c7ff",
                outline="",
                tags="bucket_cursor"
            )
            shimmer_x = bx - 5 + int((time.monotonic() * 24) % 9)
            self.left_canvas.create_line(
                shimmer_x,
                water_top + 1,
                shimmer_x + 5,
                water_top + 1,
                fill="#d8f3ff",
                width=2,
                tags="bucket_cursor"
            )
            pulse_extent = max(8, int(360 * self.bucket_fill_progress))
            self.left_canvas.create_arc(
                bx - 16,
                rim_y - 18,
                bx + 16,
                rim_y + 14,
                start=90,
                extent=-pulse_extent,
                style="arc",
                outline="#ffffff",
                width=3,
                tags="bucket_cursor"
            )
            self.left_canvas.create_text(
                bx,
                rim_y - 21,
                text=f"{int(self.bucket_fill_progress * 100)}%",
                fill="#ffffff",
                font=("Georgia", 9, "bold"),
                tags="bucket_cursor"
            )
        elif self.bucket_is_full:
            self.left_canvas.create_rectangle(
                bx - 4.8,
                rim_y + 1,
                bx + 4.8,
                rim_y + 4,
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

    def _draw_valve_wheel(self, canvas, x, y, radius, angle_deg, is_active, idx):
        ring_color = "#d6dde2" if is_active else "#b2bcc4"
        spoke_color = "#f4f7fa" if is_active else "#8f9aa2"
        tags = ("valve", f"valve_{idx}")
        canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline=ring_color,
            width=2,
            tags=tags
        )
        inner = radius * 0.32
        outer = radius * 0.86
        for k in range(4):
            theta = math.radians(angle_deg + k * 90.0)
            x0 = x + math.cos(theta) * inner
            y0 = y + math.sin(theta) * inner
            x1 = x + math.cos(theta) * outer
            y1 = y + math.sin(theta) * outer
            canvas.create_line(
                x0,
                y0,
                x1,
                y1,
                fill=spoke_color,
                width=2,
                tags=tags
            )
        canvas.create_oval(
            x - inner * 0.8,
            y - inner * 0.8,
            x + inner * 0.8,
            y + inner * 0.8,
            fill="#6f7b82",
            outline="#4f5960",
            width=1,
            tags=tags
        )

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
        self.fire_positions.pop(tag, None)
        self._draw_right_scene()

    def _format_score(self):
        return str(int(self.score))

    def _format_time(self, total_seconds):
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    root = tk.Tk()
    app = ExperimentGame(root)
    root.mainloop()
