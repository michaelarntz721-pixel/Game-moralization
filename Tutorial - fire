import math
import random
import time
import tkinter as tk

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
BG_COLOR = "#f7f4ec"
FIELD_COLOR = "#7bc96f"
WATER_LABEL_COLOR = "#d7ebfb"

FIRE_INTERVAL_MIN_MS = 2200
FIRE_INTERVAL_MAX_MS = 3800
FIRE_SIZE = 26
TIMER_SECONDS = 60


class FireTutorialGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Tutoriál - Oheň")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=BG_COLOR)

        self.time_left = TIMER_SECONDS
        self.game_over = False
        self.fires_paused = False
        self.active_fires = set()
        self.fire_counter = 0
        self.lake_bounds = (0, 0, 0, 0)

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

        self.container = tk.Frame(root, bg=BG_COLOR)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=0, minsize=132)
        self.container.rowconfigure(1, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.header = tk.Frame(self.container, bg=BG_COLOR, height=132)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        self.title_label = tk.Label(
            self.header,
            text="TUTORIÁL OHNĚ",
            font=("Trebuchet MS", 26, "bold"),
            bg=BG_COLOR,
            fg="#8b2f17",
        )
        self.title_label.place(relx=0.5, rely=0.24, anchor="center")

        self.timer_label = tk.Label(
            self.header,
            text=self._format_time(self.time_left),
            font=("Georgia", 18, "bold"),
            bg=BG_COLOR,
            fg="#2b2b2b",
        )
        self.timer_label.place(relx=0.98, rely=0.24, anchor="e")

        self.help_label = tk.Label(
            self.header,
            text=(
                "Cíl: uhasit co nejvíc ohňů. Přesuňte kbelík nad jezero a držte ho tam 2 sekundy,\n"
                "dokud se nenaplní. Potom klikněte na oheň a vylijete vodu. Na každý oheň je potřeba\n"
                "jedno plné nabití kbelíku, takže po každém uhašení musíte znovu k jezeru."
            ),
            font=("Trebuchet MS", 12, "bold"),
            bg=BG_COLOR,
            fg="#4f3c2f",
            justify="center",
            wraplength=900,
        )
        self.help_label.place(relx=0.5, rely=0.72, anchor="center")

        self.canvas = tk.Canvas(
            self.container,
            bg=FIELD_COLOR,
            highlightthickness=0,
            cursor="none",
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._draw_field)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.end_overlay = tk.Frame(self.root, bg=BG_COLOR)
        self.end_overlay.place_forget()
        self.end_title = tk.Label(
            self.end_overlay,
            text="ČAS VYPRŠEL",
            font=("Trebuchet MS", 22, "bold"),
            bg=BG_COLOR,
            fg="#4f3c2f",
        )
        self.end_title.place(relx=0.5, rely=0.34, anchor="center")
        self.end_label = tk.Label(
            self.end_overlay,
            text="Trénink hašení dokončen",
            font=("Trebuchet MS", 28, "bold"),
            bg=BG_COLOR,
            fg="#c1121f",
        )
        self.end_label.place(relx=0.5, rely=0.56, anchor="center")
        self.root.after(500, self.schedule_next_fire)
        self.root.after(1000, self.on_timer_tick)

    def schedule_next_fire(self):
        if self.fires_paused:
            return
        delay_ms = int(random.uniform(FIRE_INTERVAL_MIN_MS, FIRE_INTERVAL_MAX_MS))
        self.root.after(delay_ms, self.spawn_fire)

    def spawn_fire(self):
        if self.fires_paused:
            return
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        size = FIRE_SIZE
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
        self.schedule_next_fire()

    def on_motion(self, event):
        self.pointer_x = event.x
        self.pointer_y = event.y
        self._draw_bucket_cursor(event.x, event.y)
        if self.bucket_is_filling and not self._point_in_lake(event.x, event.y):
            self._cancel_bucket_fill()

    def on_leave(self, event):
        self.canvas.delete("bucket_cursor")
        if self.bucket_is_filling:
            self._cancel_bucket_fill()

    def on_press(self, event):
        if self.game_over:
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
                    self._start_bucket_pour_animation(
                        event.x,
                        event.y,
                        center[0],
                        center[1],
                        fire_tag,
                    )
                self.bucket_is_full = False
                self._draw_bucket_cursor(event.x, event.y)
            return

        if self._point_in_lake(event.x, event.y) and not self.bucket_is_full:
            self._start_bucket_fill()

    def on_release(self, event):
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
        self._draw_bucket_cursor(self.pointer_x, self.pointer_y)

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
        items = self.canvas.find_overlapping(x, y, x, y)
        for item_id in reversed(items):
            tags = self.canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("fire_"):
                    return tag
        return None

    def _fire_center(self, tag):
        bbox = self.canvas.bbox(tag)
        if bbox is None:
            return None
        x0, y0, x1, y1 = bbox
        return ((x0 + x1) * 0.5, (y0 + y1) * 0.5)

    def _start_bucket_pour_animation(self, source_x, source_y, target_x, target_y, fire_tag):
        if self.bucket_pour_after_id is not None:
            self.root.after_cancel(self.bucket_pour_after_id)
            self.bucket_pour_after_id = None
        self.canvas.delete("bucket_pour")
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

        self.canvas.delete("bucket_pour")
        self.canvas.create_line(
            mouth_x,
            mouth_y,
            mid_x,
            mid_y,
            tx,
            ty,
            fill="#86cff7",
            width=2,
            smooth=True,
            tags="bucket_pour",
        )
        for i in range(6):
            u = i / 5.0
            px = ((1 - u) * (1 - u) * mouth_x) + (2 * (1 - u) * u * mid_x) + (u * u * tx)
            py = ((1 - u) * (1 - u) * mouth_y) + (2 * (1 - u) * u * mid_y) + (u * u * ty)
            self.canvas.create_oval(
                px - 1.8,
                py - 1.8,
                px + 1.8,
                py + 1.8,
                fill="#a9e1ff",
                outline="",
                tags="bucket_pour",
            )
        self.canvas.tag_raise("bucket_pour")
        self.canvas.tag_raise("bucket_cursor")

        if step >= steps - 1:
            self.remove_fire(fire_tag)
            self.bucket_pour_state = None
            self.bucket_pour_after_id = self.root.after(90, lambda: self.canvas.delete("bucket_pour"))
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

    def show_end_overlay(self):
        self.end_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.end_overlay.lift()

    def end_game(self):
        if self.game_over:
            return
        self.game_over = True
        self.fires_paused = True
        if self.bucket_is_filling:
            self._cancel_bucket_fill()
        if self.bucket_pour_after_id is not None:
            self.root.after_cancel(self.bucket_pour_after_id)
            self.bucket_pour_after_id = None
        self.bucket_pour_state = None
        self.canvas.delete("bucket_pour")
        self.show_end_overlay()

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
        log_y = y + size * 0.8
        self._draw_log(x - size * 0.2, log_y, size * 2.1, size * 0.55, -18, "#8b5a2b", "#a56b35", tag)
        self._draw_log(x + size * 0.25, log_y + size * 0.08, size * 2.1, size * 0.55, 18, "#7a4a22", "#965826", tag)

        self.canvas.create_oval(
            x - size * 1.2,
            y - size * 1.0,
            x + size * 1.2,
            y + size * 0.8,
            fill="#ffd39a",
            outline="",
            tags=(tag, "fire"),
        )

        ember_w = size * 1.2
        ember_h = size * 0.35
        self.canvas.create_oval(
            x - ember_w,
            y + size * 0.35,
            x + ember_w,
            y + size * 0.35 + ember_h,
            fill="#d06b1a",
            outline="",
            tags=(tag, "fire"),
        )
        for _ in range(random.randint(4, 7)):
            ex = x + random.uniform(-ember_w * 0.6, ember_w * 0.6)
            ey = y + size * 0.45 + random.uniform(0, ember_h * 0.6)
            er = size * random.uniform(0.03, 0.07)
            self.canvas.create_oval(
                ex - er,
                ey - er,
                ex + er,
                ey + er,
                fill="#ffb347",
                outline="",
                tags=(tag, "fire"),
            )

        outer_points = self._flame_points(x, y, size * 1.15, jitter=0.14)
        self.canvas.create_polygon(*outer_points, fill="#ff6a00", outline="", smooth=True, tags=(tag, "fire"))

        mid_points = self._flame_points(x, y + size * 0.08, size * 0.85, jitter=0.12)
        self.canvas.create_polygon(*mid_points, fill="#ff9f1a", outline="", smooth=True, tags=(tag, "fire"))

        inner_points = self._flame_points(x, y + size * 0.12, size * 0.6, jitter=0.1)
        self.canvas.create_polygon(*inner_points, fill="#ffd166", outline="", smooth=True, tags=(tag, "fire"))

        core_size = size * 0.18
        self.canvas.create_oval(
            x - core_size,
            y - core_size * 1.2,
            x + core_size,
            y + core_size * 0.7,
            fill="#fff3b0",
            outline="",
            tags=(tag, "fire"),
        )

        for _ in range(random.randint(2, 4)):
            sx = x + random.uniform(-size * 0.6, size * 0.6)
            sy = y - random.uniform(size * 0.5, size * 1.2)
            r = size * random.uniform(0.05, 0.12)
            self.canvas.create_oval(
                sx - r,
                sy - r,
                sx + r,
                sy + r,
                fill="#ffe8a3",
                outline="",
                tags=(tag, "fire"),
            )

    def _draw_field(self, event):
        width = event.width
        height = event.height
        self.canvas.delete("grass")
        self.canvas.delete("lake")
        self.canvas.create_rectangle(0, 0, width, height, fill=FIELD_COLOR, outline="", tags="grass")

        for y in range(0, height, 6):
            shade = "#6dbb63" if (y // 6) % 2 == 0 else "#76c56a"
            self.canvas.create_line(0, y, width, y, fill=shade, tags="grass")

        for y in range(8, height, 18):
            for x in range(6, width, 22):
                blade_h = random.randint(6, 10)
                jitter = random.randint(-2, 2)
                self.canvas.create_line(x + jitter, y, x + jitter, y - blade_h, fill="#5fae58", tags="grass")

        for y in range(14, height, 24):
            for x in range(14, width, 28):
                blade_h = random.randint(8, 14)
                jitter = random.randint(-3, 3)
                self.canvas.create_line(
                    x + jitter,
                    y,
                    x + jitter - 4,
                    y - blade_h,
                    fill="#63b65d",
                    tags="grass",
                )

        for y in range(10, height, 16):
            for x in range(10, width, 18):
                blade_h = random.randint(5, 9)
                jitter = random.randint(-2, 2)
                self.canvas.create_line(
                    x + jitter,
                    y + 2,
                    x + jitter + 3,
                    y - blade_h,
                    fill="#5aa854",
                    tags="grass",
                )

        lake_w = max(170, int(width * 0.25))
        lake_h = max(100, int(height * 0.18))
        lake_x0 = int(width * 0.06)
        lake_y0 = int(height * 0.74)
        lake_x1 = min(width - 20, lake_x0 + lake_w)
        lake_y1 = min(height - 10, lake_y0 + lake_h)
        self.lake_bounds = (lake_x0, lake_y0, lake_x1, lake_y1)

        self.canvas.create_oval(
            lake_x0,
            lake_y0,
            lake_x1,
            lake_y1,
            fill="#3b82c4",
            outline="#2d5f8f",
            width=2,
            tags="lake",
        )
        self.canvas.create_oval(
            lake_x0 + 14,
            lake_y0 + 10,
            lake_x1 - 14,
            lake_y1 - 16,
            fill="#6eb6e8",
            outline="",
            tags="lake",
        )
        self.canvas.create_text(
            (lake_x0 + lake_x1) * 0.5,
            (lake_y0 + lake_y1) * 0.5,
            text="JEZERO",
            fill=WATER_LABEL_COLOR,
            font=("Georgia", 12, "bold"),
            tags="lake",
        )

        self.canvas.tag_lower("grass")
        self.canvas.tag_raise("lake")
        self.canvas.tag_raise("fire")
        self._draw_bucket_cursor(self.pointer_x, self.pointer_y)

    def _draw_bucket_cursor(self, x, y):
        if x <= 0 and y <= 0:
            return
        self.canvas.delete("bucket_cursor")
        bx = x + 12
        by = y + 12

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

        self.canvas.create_line(
            left_lug_x,
            lug_y,
            bx,
            rim_y - 12,
            right_lug_x,
            lug_y,
            fill="#555555",
            width=2,
            smooth=True,
            tags="bucket_cursor",
        )
        self.canvas.create_oval(
            left_lug_x - lug_r,
            lug_y - lug_r,
            left_lug_x + lug_r,
            lug_y + lug_r,
            fill="#8e98a2",
            outline="#555555",
            width=1,
            tags="bucket_cursor",
        )
        self.canvas.create_oval(
            right_lug_x - lug_r,
            lug_y - lug_r,
            right_lug_x + lug_r,
            lug_y + lug_r,
            fill="#8e98a2",
            outline="#555555",
            width=1,
            tags="bucket_cursor",
        )

        self.canvas.create_line(
            bx - top_w * 0.5,
            rim_y,
            bx + top_w * 0.5,
            rim_y,
            fill="#2e5870" if self.bucket_is_filling else "#555555",
            width=3 if self.bucket_is_filling else 2,
            tags="bucket_cursor",
        )
        self.canvas.create_polygon(
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
            tags="bucket_cursor",
        )

        if self.bucket_is_filling:
            fill_height = int((body_h - 2) * self.bucket_fill_progress)
            water_top = rim_y + body_h - 1 - fill_height
            self.canvas.create_rectangle(
                bx - 5.5,
                water_top,
                bx + 5.5,
                rim_y + body_h - 1,
                fill="#57c7ff",
                outline="",
                tags="bucket_cursor",
            )
            shimmer_x = bx - 5 + int((time.monotonic() * 24) % 9)
            self.canvas.create_line(
                shimmer_x,
                water_top + 1,
                shimmer_x + 5,
                water_top + 1,
                fill="#d8f3ff",
                width=2,
                tags="bucket_cursor",
            )
            pulse_extent = max(8, int(360 * self.bucket_fill_progress))
            self.canvas.create_arc(
                bx - 16,
                rim_y - 18,
                bx + 16,
                rim_y + 14,
                start=90,
                extent=-pulse_extent,
                style="arc",
                outline="#ffffff",
                width=3,
                tags="bucket_cursor",
            )
            self.canvas.create_text(
                bx,
                rim_y - 21,
                text=f"{int(self.bucket_fill_progress * 100)}%",
                fill="#ffffff",
                font=("Georgia", 9, "bold"),
                tags="bucket_cursor",
            )
        elif self.bucket_is_full:
            self.canvas.create_rectangle(
                bx - 4.8,
                rim_y + 1,
                bx + 4.8,
                rim_y + 4,
                fill="#86cff7",
                outline="",
                tags="bucket_cursor",
            )
        self.canvas.tag_raise("bucket_cursor")

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

    def _draw_log(self, x, y, length, thickness, angle_deg, color, highlight, tag):
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
        self.canvas.create_polygon(*points, fill=color, outline="", smooth=True, tags=(tag, "fire"))

        inner_points = []
        inner_scale = 0.6
        for cx, cy in corners:
            cx *= inner_scale
            cy *= inner_scale
            rx = cx * math.cos(angle) - cy * math.sin(angle)
            ry = cx * math.sin(angle) + cy * math.cos(angle)
            inner_points.extend([x + rx, y + ry])
        self.canvas.create_polygon(*inner_points, fill=highlight, outline="", smooth=True, tags=(tag, "fire"))

    def remove_fire(self, tag):
        self.canvas.delete(tag)
        if tag in self.active_fires:
            self.active_fires.remove(tag)

    def _format_time(self, total_seconds):
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    root = tk.Tk()
    app = FireTutorialGame(root)
    root.mainloop()
