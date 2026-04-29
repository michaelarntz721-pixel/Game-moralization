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
        self.tutorial_end_delay_ms = 1600
        self.root = root
        self.root.title("Tutorial - Ohně")
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
        self.countdown_running = False
        self.countdown_value = 0
        self.countdown_after_id = None
        self.countdown_overlay = None
        self.countdown_overlay_label = None
        self.countdown_overlay_bg = "#ff00ff"
        self.tutorial_end_after_id = None

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
            padx=30,
            pady=30,
        )
        self.info_panel.grid(row=0, column=1, sticky="nsew")

        self.title_label = tk.Label(
            self.info_panel,
            text="Tutorial - Ohně",
            font=("Georgia", 28, "bold"),
            bg=RIGHT_BG,
            fg="#8b2f17",
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
            fg="#c1121f",
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
            text="Tutorial - Ohně",
            font=("Georgia", 34, "bold"),
            bg=RIGHT_BG,
            fg="#8b2f17",
        )
        self.start_title_label.place(relx=0.5, rely=0.42, anchor="center")
        self.start_hint_label = tk.Label(
            self.start_overlay,
            text="Stiskněte mezerník a projděte si ovládání hašení ohně",
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
        self.root.after(150, self._show_initial_bucket_cursor)

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
                "Před sebou vidíte louku, na které se budou objevovat ohně.\n"
                "K jejich hašení budete používat jezero jako zdroj vody a kyblík jako nástroj pro přenášení vody.",
                "Stiskněte mezerník a přejděte k nácviku plnění kyblíku.",
            ),
            (
                "Kyblík naplníte tak, že najedete kurzorem nad jezero, stisknete levé tlačítko myši "
                "a podržíte ho 2 vteřiny. Pokud tlačítko pustíte dříve, "
                "plnění se jen zastaví a po dalším stisku pokračuje od stejné úrovně.\n\n"
                "Teď si plnění kyblíku vyzkoušejte.",
                (
                    "Máte hotovo. Stiskněte mezerník a přejděte k hašení ohně."
                    if self.bucket_fill_practiced
                    else "Najeďte nad jezero, podržte tlačítko a naplňte kyblík."
                ),
            ),
            (
                "Plný kyblík stačí vždy jen na uhašení jednoho ohně. "
                "Po každém uhašení je proto potřeba vrátit se k jezeru a znovu ho naplnit. "
                "V tomto kroku na vás čekají dva ohně, takže celý postup provedete dvakrát.\n\n"
                "Teď si zkuste celý postup v praxi.",
                "Naplňte kyblík a uhaste oba ohně na louce.",
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
        if self.game_over:
            return
        if self.tutorial_stage == -1:
            self.tutorial_stage = 0
            self.start_overlay.place_forget()
            self._show_initial_bucket_cursor()
            self._update_stage_text()
        elif self.tutorial_stage == 0:
            self.tutorial_stage = 1
            self._cancel_bucket_fill()
            self.bucket_is_full = False
            self.bucket_fill_progress = 0.0
            self.bucket_fill_practiced = False
            self.left_canvas.delete("bucket_cursor")
            self._update_stage_text()
        elif self.tutorial_stage == 1 and self.bucket_fill_practiced:
            self.tutorial_stage = 2
            self._cancel_bucket_fill()
            self.bucket_is_full = False
            self.bucket_fill_progress = 0.0
            self.left_canvas.delete("bucket_cursor")
            self._spawn_tutorial_fires()
            self._update_stage_text()

    def on_enter_press(self, event=None):
        if self.game_over and self.end_overlay.winfo_ismapped():
            self.restart_tutorial()

    def restart_tutorial(self):
        if self.tutorial_end_after_id is not None:
            self.root.after_cancel(self.tutorial_end_after_id)
            self.tutorial_end_after_id = None
        if self.bucket_fill_after_id is not None or self.bucket_fill_anim_after_id is not None:
            self._cancel_bucket_fill()
        if self.bucket_pour_after_id is not None:
            self.root.after_cancel(self.bucket_pour_after_id)
            self.bucket_pour_after_id = None
        self.bucket_pour_state = None
        self.game_over = False
        self.fires_paused = False
        self.bucket_is_full = False
        self.bucket_fill_practiced = False
        self.bucket_fill_progress = 0.0
        self.left_mouse_down = False
        self.pointer_x = 0
        self.pointer_y = 0
        self.tutorial_stage = -1
        self.active_fires.clear()
        self.fire_positions.clear()
        self.end_overlay.place_forget()
        self.left_canvas.delete("fire")
        self.left_canvas.delete("bucket_cursor")
        self.left_canvas.delete("bucket_pour")
        self.left_canvas.delete("bucket_fill_ring")
        self.left_canvas.delete("sprinkler_splash")
        self.start_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.start_overlay.lift()
        self._update_stage_text()
        self.root.after(150, self._show_initial_bucket_cursor)

    def schedule_next_fire(self):
        return

    def update_score(self, delta):
        return

    def _draw_right_scene(self, event=None):
        return

    def _show_initial_bucket_cursor(self):
        self.left_canvas.update_idletasks()
        width = self.left_canvas.winfo_width()
        height = self.left_canvas.winfo_height()
        if width <= 1 or height <= 1:
            self.root.after(100, self._show_initial_bucket_cursor)
            return
        self.pointer_x = int(width * 0.5)
        self.pointer_y = int(height * 0.55)
        self._draw_bucket_cursor(self.pointer_x, self.pointer_y)

    def on_left_motion(self, event):
        if self.game_over:
            return
        super().on_left_motion(event)

    def on_left_leave(self, event):
        if self.game_over:
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

    def _spawn_tutorial_fires(self):
        self.left_canvas.update_idletasks()
        width = self.left_canvas.winfo_width()
        height = self.left_canvas.winfo_height()
        if width <= 1 or height <= 1:
            self.root.after(100, self._spawn_tutorial_fires)
            return
        self.left_canvas.delete("fire")
        self.active_fires.clear()
        self.fire_positions.clear()
        positions = (
            (0.42, 0.42),
            (0.62, 0.56),
        )
        size = 26
        for rel_x, rel_y in positions:
            self.fire_counter += 1
            tag = f"fire_{self.fire_counter}"
            x = int(width * rel_x)
            y = int(height * rel_y)
            self._draw_fire(x, y, size, tag)
            self.active_fires.add(tag)
            self.fire_positions[tag] = (x, y, size)
        self.left_canvas.tag_raise("fire")
        self.left_canvas.tag_raise("bucket_cursor")

    def remove_fire(self, tag):
        ExperimentGame.remove_fire(self, tag)
        if self.tutorial_stage == 2 and not self.active_fires:
            self._schedule_tutorial_complete()

    def _schedule_tutorial_complete(self):
        if self.tutorial_end_after_id is not None:
            return
        self.game_over = True
        self.fires_paused = True
        self.tutorial_end_after_id = self.root.after(
            self.tutorial_end_delay_ms,
            self._finish_tutorial_complete,
        )

    def _finish_tutorial_complete(self):
        self.tutorial_end_after_id = None
        if self.bucket_is_filling:
            self._cancel_bucket_fill()
        self.bucket_pour_state = None
        self.show_end_overlay()

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
