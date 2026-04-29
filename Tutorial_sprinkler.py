# -*- coding: utf-8 -*-
import tkinter as tk

from experiment_game import (
    ExperimentGame,
    RIGHT_BG,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class SprinklerTutorialGame(ExperimentGame):
    def __init__(self, root):
        self.tutorial_end_delay_ms = 3200
        self.root = root
        self.root.title("Tutorial - Zavlažovací systém")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=RIGHT_BG)

        self.game_started = True
        self.game_over = False
        self.fires_paused = False
        self.score = 0

        self.active_fires = set()
        self.fire_positions = {}
        self.fire_counter = 0

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
        self.countdown_overlay = None
        self.countdown_overlay_label = None
        self.countdown_overlay_bg = "#ff00ff"
        self.countdown_running = False
        self.countdown_value = 0
        self.countdown_after_id = None

        self.tutorial_stage = -1
        self.first_segment_done = False
        self.stage_two_ready = False

        self.container = tk.Frame(root, bg=RIGHT_BG)
        self.container.pack(fill="both", expand=True)
        self.container.columnconfigure(0, weight=1, uniform="half")
        self.container.columnconfigure(1, weight=1, uniform="half")
        self.container.rowconfigure(0, weight=1)

        self.info_panel = tk.Frame(
            self.container,
            bg=RIGHT_BG,
            padx=30,
            pady=30,
        )
        self.info_panel.grid(row=0, column=0, sticky="nsew")

        self.title_label = tk.Label(
            self.info_panel,
            text="Tutorial - Zavlažovací systém",
            font=("Georgia", 28, "bold"),
            bg=RIGHT_BG,
            fg="#37515e",
        )
        self.title_label.pack(anchor="center", pady=(20, 20))

        self.instructions_wraplength = 520
        self.stage_blocks = []
        for _ in range(3):
            block = tk.Frame(self.info_panel, bg=RIGHT_BG)
            block.pack(anchor="n", fill="x", pady=(0, 18))

            body_label = tk.Label(
                block,
                text="",
                font=("Trebuchet MS", 16, "bold"),
                bg=RIGHT_BG,
                fg="#4f3c2f",
                justify="left",
                wraplength=self.instructions_wraplength,
            )
            body_label.pack(anchor="w", fill="x")

            hint_label = tk.Label(
                block,
                text="",
                font=("Trebuchet MS", 14, "bold"),
                bg=RIGHT_BG,
                fg="#37515e",
                justify="left",
                wraplength=self.instructions_wraplength,
            )
            hint_label.pack(anchor="w", fill="x", pady=(14, 0))
            self.stage_blocks.append((body_label, hint_label))

        self.right_frame = tk.Frame(self.container, bg=RIGHT_BG)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self._build_right_scene()
        self.valve_hold_ms = 15000

        self.end_overlay = tk.Frame(self.root, bg=RIGHT_BG)
        self.end_overlay.place_forget()
        self.end_title = tk.Label(
            self.end_overlay,
            text="TUTORIÁL DOKONČEN",
            font=("Trebuchet MS", 24, "bold"),
            bg=RIGHT_BG,
            fg="#4f3c2f",
        )
        self.end_title.place(relx=0.5, rely=0.40, anchor="center")
        self.end_label = tk.Label(
            self.end_overlay,
            text="Tutoriál je hotový. Můžete pokračovat do hlavní části experimentu, nebo si ho projít ještě jednou.",
            font=("Trebuchet MS", 18, "bold"),
            bg=RIGHT_BG,
            fg="#2f78b2",
            justify="center",
            wraplength=1040,
        )
        self.end_label.place(relx=0.5, rely=0.54, anchor="center")
        self.end_hint = tk.Label(
            self.end_overlay,
            text="Enter = zkusit tutorial znovu, mezerník = ukončit tutorial",
            font=("Trebuchet MS", 16, "bold"),
            bg=RIGHT_BG,
            fg="#4f3c2f",
            justify="center",
            wraplength=1040,
        )
        self.end_hint.place(relx=0.5, rely=0.66, anchor="center")

        self.start_overlay = tk.Frame(self.root, bg=RIGHT_BG)
        self.start_title_label = tk.Label(
            self.start_overlay,
            text="Tutorial - Zavlažovací systém",
            font=("Georgia", 34, "bold"),
            bg=RIGHT_BG,
            fg="#37515e",
        )
        self.start_title_label.place(relx=0.5, rely=0.42, anchor="center")
        self.start_hint_label = tk.Label(
            self.start_overlay,
            text="Stiskněte mezerník a projděte si ovládání zavlažovacího systému",
            font=("Trebuchet MS", 18, "bold"),
            bg=RIGHT_BG,
            fg="#4f3c2f",
            justify="center",
            wraplength=1040,
        )
        self.start_hint_label.place(relx=0.5, rely=0.54, anchor="center")
        self.start_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.start_overlay.lift()

        self.root.bind_all("<KeyPress-space>", self.on_space_press)
        self.root.bind_all("<KeyPress-Return>", self.on_enter_press)
        self.root.bind_all("<KeyPress-KP_Enter>", self.on_enter_press)
        self.info_panel.bind("<Configure>", self._resize_instruction_wraps)
        self.root.after(100, self.root.focus_force)
        self._update_stage_text()
        self._draw_right_scene()

    def _resize_instruction_wraps(self, event=None):
        panel_width = event.width if event is not None else self.info_panel.winfo_width()
        wraplength = max(420, min(540, panel_width - 90))
        if wraplength == self.instructions_wraplength:
            return
        self.instructions_wraplength = wraplength
        for body_label, hint_label in self.stage_blocks:
            body_label.config(wraplength=wraplength)
            hint_label.config(wraplength=wraplength)

    def _update_stage_text(self):
        stage_texts = [
            (
                "Na pravé straně vidíte zavlažovací systém, ve kterém zatím není dostatečný tlak. "
                "Vaším úkolem bude postupně aktivovat ventily, zvednout hladinu vody v potrubí "
                "a tím spustit zavlažovací systém.",
                "Stiskněte mezerník a přejděte k praktické ukázce.",
            ),
            (
                "Ventil aktivujete tak, že na něj najedete myší, kliknete levým tlačítkem myši "
                "a podržíte ho 15 vteřin. "
                "Postup uvidíte na stoupajícím modrém sloupci vody v potrubí. "
                "Ventily je potřeba aktivovat postupně podle čísel od 1 do 4.",
                (
                    "První úroveň je hotová. Stiskněte mezerník a přejděte k závěrečnému kroku."
                    if self.first_segment_done
                    else "Začněte ventilem 1 a sledujte, jak modrá voda stoupá do první úrovně."
                ),
            ),
            (
                "Každý správně aktivovaný ventil zvýší hladinu vody o jednu úroveň. "
                "Stoupající modrý sloupec vody ukazuje, jak blízko jste k dokončení aktuálního kroku. "
                "Jakmile dokončíte i poslední ventil, systém získá plný tlak a zavlažovací systém se automaticky spustí.",
                "Dokončete aktivaci ventilu 4, sledujte stoupající vodu a potom spuštění zavlažování.",
            ),
        ]

        inactive_body = "#94897f"
        inactive_hint = "#aaa39b"
        active_body = "#4f3c2f"
        active_hint = "#37515e"

        for idx, (body_label, hint_label) in enumerate(self.stage_blocks):
            if idx > self.tutorial_stage:
                body_label.config(text="")
                hint_label.config(text="")
            else:
                body_text, hint_text = stage_texts[idx]
                is_active = idx == self.tutorial_stage
                body_label.config(
                    text=body_text,
                    fg=active_body if is_active else inactive_body,
                )
                hint_label.config(
                    text=hint_text,
                    fg=active_hint if is_active else inactive_hint,
                )

    def on_space_press(self, event=None):
        if self.game_over and self.end_overlay.winfo_ismapped():
            self.root.destroy()
            return
        if self.game_over and self.sprinkler_on:
            return
        if self.tutorial_stage == -1:
            self.tutorial_stage = 0
            self.start_overlay.place_forget()
            self._update_stage_text()
            self._draw_right_scene()
        elif self.tutorial_stage == 0:
            self.tutorial_stage = 1
            self.first_segment_done = False
            self.completed_valves = 0
            self.active_valve_index = None
            self.active_valve_progress = 0.0
            self.sprinkler_on = False
            self.game_over = False
            self._update_stage_text()
            self._draw_right_scene()
        elif self.tutorial_stage == 1 and self.first_segment_done:
            self.tutorial_stage = 2
            self.stage_two_ready = True
            self.completed_valves = 3
            self.active_valve_index = None
            self.active_valve_progress = 0.0
            self.sprinkler_on = False
            self.game_over = False
            self._update_stage_text()
            self._draw_right_scene()

    def on_enter_press(self, event=None):
        if self.game_over and self.end_overlay.winfo_ismapped():
            self.restart_tutorial()

    def restart_tutorial(self):
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self.game_over = False
        self.fires_paused = False
        self.sprinkler_on = False
        self.completed_valves = 0
        self.active_valve_index = None
        self.active_valve_progress = 0.0
        self.active_valve_start = 0.0
        self.tutorial_stage = -1
        self.first_segment_done = False
        self.stage_two_ready = False
        self.end_overlay.place_forget()
        self.start_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.start_overlay.lift()
        self._update_stage_text()
        self._draw_right_scene()

    def on_right_press(self, event):
        if self.tutorial_stage not in (1, 2):
            return
        if self.game_over or self.sprinkler_on:
            return
        if self.tutorial_stage == 1 and self.first_segment_done:
            return
        valve_index = self._right_valve_index_at(event.x, event.y)
        if valve_index is None or valve_index != self.completed_valves:
            return
        self.active_valve_index = valve_index
        self.active_valve_start = self._monotonic() - (
            self.active_valve_progress * (self.valve_hold_ms / 1000.0)
        )
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self._tick_valve_hold()

    def _monotonic(self):
        import time

        return time.monotonic()

    def _tick_valve_hold(self):
        if self.active_valve_index is None or self.sprinkler_on:
            self.valve_hold_after_id = None
            return
        elapsed = self._monotonic() - self.active_valve_start
        self.active_valve_progress = max(0.0, min(1.0, elapsed / (self.valve_hold_ms / 1000.0)))
        if self.active_valve_progress >= 1.0:
            self.completed_valves += 1
            self.active_valve_index = None
            self.active_valve_progress = 0.0
            self.valve_hold_after_id = None
            if self.tutorial_stage == 1:
                self.first_segment_done = True
                self._update_stage_text()
                self._draw_right_scene()
                return
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
        elapsed = self._monotonic() - self.active_valve_start
        self.active_valve_progress = max(0.0, min(1.0, elapsed / (self.valve_hold_ms / 1000.0)))
        self.active_valve_index = None
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self._draw_right_scene()

    def _draw_right_scene(self, event=None):
        ExperimentGame._draw_right_scene(self, event)
        if not hasattr(self, "right_canvas"):
            return

        canvas = self.right_canvas
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        if self.tutorial_stage == 1 and not self.first_segment_done:
            self._draw_target_arrow(0)
            self._draw_water_progress_arrow()
        elif self.tutorial_stage == 2 and not self.sprinkler_on:
            self._draw_target_arrow(3)
            self._draw_water_progress_arrow()

        if self.tutorial_stage == 1 and self.first_segment_done:
            canvas.create_rectangle(
                w * 0.16,
                h - 60,
                w * 0.84,
                h - 12,
                fill="#7a5634",
                outline="",
            )
            canvas.create_text(
                w * 0.5,
                h - 36,
                text="První segment je hotový. Pokračujte mezerníkem.",
                fill="#f6e7d2",
                font=("Trebuchet MS", 13, "bold"),
                justify="center",
                width=int(w * 0.62),
            )

    def _draw_target_arrow(self, valve_index):
        if valve_index >= len(self.valve_centers):
            return
        canvas = self.right_canvas
        vx, vy = self.valve_centers[valve_index]
        start_x = vx - 118
        start_y = vy - 50
        end_x = vx - self.valve_radius - 6
        end_y = vy
        label_x = start_x - 2
        label_y = start_y - 22
        label_pad_x = 16
        label_pad_y = 8
        canvas.create_line(
            start_x,
            start_y,
            end_x,
            end_y,
            fill="#fff4d6",
            width=11,
            arrow="last",
            arrowshape=(22, 24, 10),
            capstyle="round",
            joinstyle="round",
            tags="tutorial_arrow",
        )
        canvas.create_line(
            start_x,
            start_y,
            end_x,
            end_y,
            fill="#d62828",
            width=7,
            arrow="last",
            arrowshape=(20, 22, 9),
            capstyle="round",
            joinstyle="round",
            tags="tutorial_arrow",
        )
        canvas.create_rectangle(
            label_x - label_pad_x,
            label_y - label_pad_y,
            label_x + 34,
            label_y + 14,
            fill="#fff4d6",
            outline="#d62828",
            width=3,
            tags="tutorial_arrow",
        )
        canvas.create_text(
            label_x,
            label_y + 2,
            text="ZDE",
            fill="#d62828",
            font=("Trebuchet MS", 13, "bold"),
            anchor="w",
            tags="tutorial_arrow",
        )

    def _draw_water_progress_arrow(self):
        canvas = self.right_canvas
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        ground_y = max(70, int(h * 0.2))
        grass_h = max(14, int(h * 0.03))
        dirt_top = ground_y + grass_h
        pipe_x = w * 0.5
        pipe_w = max(28, int(w * 0.08))
        pipe_top = dirt_top + 10
        pipe_bottom = int(h * 0.82)
        riser_top = max(10, ground_y - 22)
        level_spacing = (pipe_bottom - riser_top) / float(self.valve_total)
        valve_ys = [pipe_bottom - (level_spacing * (idx + 1)) for idx in range(self.valve_total)]

        if self.sprinkler_on:
            target_y = riser_top
        else:
            water_stages = [pipe_bottom] + valve_ys
            stage_index = min(self.completed_valves, self.valve_total - 1)
            start_top = water_stages[stage_index]
            end_top = water_stages[stage_index + 1]
            progress = self.active_valve_progress
            water_top = start_top + ((end_top - start_top) * progress)
            target_y = water_top if progress > 0.04 else start_top - ((start_top - end_top) * 0.35)

        target_y = max(riser_top + 10, min(pipe_bottom - 18, target_y))
        start_x = pipe_x - pipe_w * 2.25
        start_y = target_y - 44
        end_x = pipe_x - pipe_w * 0.32
        end_y = target_y
        label_x = start_x - 4
        label_y = start_y - 24
        label_pad_x = 14
        label_pad_y = 8

        canvas.create_line(
            start_x,
            start_y,
            end_x,
            end_y,
            fill="#e5f7ff",
            width=11,
            arrow="last",
            arrowshape=(22, 24, 10),
            capstyle="round",
            joinstyle="round",
            tags="tutorial_arrow",
        )
        canvas.create_line(
            start_x,
            start_y,
            end_x,
            end_y,
            fill="#1479b8",
            width=7,
            arrow="last",
            arrowshape=(20, 22, 9),
            capstyle="round",
            joinstyle="round",
            tags="tutorial_arrow",
        )
        canvas.create_rectangle(
            label_x - label_pad_x,
            label_y - label_pad_y,
            label_x + 78,
            label_y + 14,
            fill="#e5f7ff",
            outline="#1479b8",
            width=3,
            tags="tutorial_arrow",
        )
        canvas.create_text(
            label_x,
            label_y + 2,
            text="POSTUP",
            fill="#1479b8",
            font=("Trebuchet MS", 13, "bold"),
            anchor="w",
            tags="tutorial_arrow",
        )

    def _activate_sprinkler(self):
        if self.sprinkler_on:
            return
        self.sprinkler_on = True
        self.game_over = True
        if self.valve_hold_after_id is not None:
            self.root.after_cancel(self.valve_hold_after_id)
            self.valve_hold_after_id = None
        self.active_valve_index = None
        self.active_valve_progress = 0.0
        self._draw_right_scene()
        self.root.after(self.tutorial_end_delay_ms, self.show_end_overlay)

    def show_end_overlay(self):
        self.end_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.end_overlay.lift()


if __name__ == "__main__":
    root = tk.Tk()
    app = SprinklerTutorialGame(root)
    root.mainloop()
