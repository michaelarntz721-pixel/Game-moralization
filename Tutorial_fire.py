# -*- coding: utf-8 -*-
import tkinter as tk

from experiment_game import (
    ExperimentGame,
    LEFT_BG,
    RIGHT_BG,
    RIGHT_PANEL_PADDING,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class FireTutorialGame(ExperimentGame):
    def __init__(self, root):
        self.root = root
        self.root.title("Tutoriál - Oheň")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=RIGHT_BG)

        self.game_started = True
        self.game_over = False
        self.fires_paused = False
        self.score = 0

        self.active_fires = set()
        self.fire_positions = {}
        self.fire_counter = 0
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

        self.valve_hold_after_id = None
        self.sprinkler_anim_after_id = None
        self.sprinkler_animating = False
        self.sprinkler_anim_end_at = 0.0
        self.sprinkler_next_extinguish_at = 0.0
        self.sprinkler_pending_fires = []
        self.finish_overlay_after_sprinkler = False

        self.tutorial_stage = -1
        self.bucket_fill_practiced = False

        self.container = tk.Frame(root, bg=RIGHT_BG)
        self.container.pack(fill="both", expand=True)
        self.container.columnconfigure(0, weight=1, uniform="half")
        self.container.columnconfigure(1, weight=1, uniform="half")
        self.container.rowconfigure(0, weight=1)

        self.left_canvas = tk.Canvas(
            self.container,
            bg=LEFT_BG,
            highlightthickness=0,
            cursor="none",
        )
        self.left_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=RIGHT_PANEL_PADDING,
            pady=RIGHT_PANEL_PADDING,
        )
        self.left_canvas.bind("<Configure>", self._draw_grass_background)
        self.left_canvas.bind("<Motion>", self.on_left_motion)
        self.left_canvas.bind("<Leave>", self.on_left_leave)
        self.left_canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.left_canvas.bind("<ButtonRelease-1>", self.on_left_release)

        self.info_panel = tk.Frame(
            self.container,
            bg=RIGHT_BG,
            padx=28,
            pady=28,
        )
        self.info_panel.grid(row=0, column=1, sticky="nsew")

        self.title_label = tk.Label(
            self.info_panel,
            text="TUTORIÁL OHNĚ",
            font=("Georgia", 28, "bold"),
            bg=RIGHT_BG,
            fg="#8b2f17",
        )
        self.title_label.pack(anchor="center", pady=(26, 22))

        self.instructions_wraplength = 420
        self.stage_blocks = []
        for _ in range(3):
            block = tk.Frame(self.info_panel, bg=RIGHT_BG)
            block.pack(anchor="n", fill="x", pady=(0, 22))

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
            text="Teď už můžete hasit oheň v hlavní části experimentu.",
            font=("Trebuchet MS", 18, "bold"),
            bg=RIGHT_BG,
            fg="#c1121f",
        )
        self.end_label.place(relx=0.5, rely=0.54, anchor="center")

        self.start_overlay = tk.Frame(self.root, bg=RIGHT_BG)
        self.start_title_label = tk.Label(
            self.start_overlay,
            text="TUTORIÁL OHNĚ",
            font=("Georgia", 34, "bold"),
            bg=RIGHT_BG,
            fg="#8b2f17",
        )
        self.start_title_label.place(relx=0.5, rely=0.42, anchor="center")
        self.start_hint_label = tk.Label(
            self.start_overlay,
            text="Zmáčknutím mezerníku zahájíte tutorial",
            font=("Trebuchet MS", 18, "bold"),
            bg=RIGHT_BG,
            fg="#4f3c2f",
        )
        self.start_hint_label.place(relx=0.5, rely=0.54, anchor="center")
        self.start_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.start_overlay.lift()

        self.root.bind_all("<KeyPress-space>", self.on_space_press)
        self.root.after(100, self.root.focus_force)
        self._update_stage_text()

    def _update_stage_text(self):
        stage_texts = [
            (
                "Před sebou vidíte louku, na které se budou objevovat ohně.\n"
                "Ohně můžete hasit za pomoci jezera a kyblíku.",
                "Zmáčkněte mezerník pro pokračování.",
            ),
            (
                "Kyblík můžete naplnit tak, že myší přejedete nad jezero, "
                "zmáčknete a 2 vteřiny držíte. Pokud pustíte tlačítko, než se "
                "kyblík celý naplní, tak musíte začít odznova.\n\n"
                "Teď si to, prosím, vyzkoušejte.",
                (
                    "Poté co jste si to vyzkoušeli, zmáčkněte mezerník pro pokračování."
                    if self.bucket_fill_practiced
                    else "Nejprve si zkuste naplnit kyblík."
                ),
            ),
            (
                "Když máte kyblík naplněný, tak jím můžete uhasit právě jeden oheň. "
                "Potom je zapotřebí opět kyblík naplnit.\n\n"
                "Nyní si to vyzkoušejte.",
                "Naplňte kyblík a uhaste oheň uprostřed pole.",
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
        if self.game_over:
            return
        if self.tutorial_stage == -1:
            self.tutorial_stage = 0
            self.start_overlay.place_forget()
            self._update_stage_text()
        elif self.tutorial_stage == 0:
            self.tutorial_stage = 1
            self.bucket_is_full = False
            self.bucket_fill_practiced = False
            self.left_canvas.delete("bucket_cursor")
            self._update_stage_text()
        elif self.tutorial_stage == 1 and self.bucket_fill_practiced:
            self.tutorial_stage = 2
            self.bucket_is_full = False
            self.bucket_fill_progress = 0.0
            self._cancel_bucket_fill()
            self.left_canvas.delete("bucket_cursor")
            self._spawn_center_fire()
            self._update_stage_text()

    def schedule_next_fire(self):
        return

    def update_score(self, delta):
        return

    def _draw_right_scene(self, event=None):
        return

    def on_left_motion(self, event):
        if self.tutorial_stage == 0 or self.game_over:
            return
        super().on_left_motion(event)

    def on_left_leave(self, event):
        if self.tutorial_stage == 0 or self.game_over:
            self.left_canvas.delete("bucket_cursor")
            return
        super().on_left_leave(event)

    def on_left_press(self, event):
        if self.tutorial_stage == 0 or self.game_over:
            return
        super().on_left_press(event)

    def on_left_release(self, event):
        if self.tutorial_stage == 0 or self.game_over:
            return
        super().on_left_release(event)

    def _finish_bucket_fill(self):
        ExperimentGame._finish_bucket_fill(self)
        if self.tutorial_stage == 1 and self.bucket_is_full:
            self.bucket_fill_practiced = True
            self._update_stage_text()

    def _spawn_center_fire(self):
        self.left_canvas.update_idletasks()
        width = self.left_canvas.winfo_width()
        height = self.left_canvas.winfo_height()
        if width <= 1 or height <= 1:
            self.root.after(100, self._spawn_center_fire)
            return
        self.left_canvas.delete("fire")
        self.active_fires.clear()
        self.fire_positions.clear()
        self.fire_counter += 1
        tag = f"fire_{self.fire_counter}"
        x = int(width * 0.5)
        y = int(height * 0.46)
        size = 26
        self._draw_fire(x, y, size, tag)
        self.active_fires.add(tag)
        self.fire_positions[tag] = (x, y, size)
        self.left_canvas.tag_raise("fire")
        self.left_canvas.tag_raise("bucket_cursor")

    def remove_fire(self, tag):
        ExperimentGame.remove_fire(self, tag)
        if self.tutorial_stage == 2 and not self.active_fires:
            self.end_game()

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
        self.left_canvas.delete("bucket_pour")
        self.show_end_overlay()


if __name__ == "__main__":
    root = tk.Tk()
    app = FireTutorialGame(root)
    root.mainloop()
