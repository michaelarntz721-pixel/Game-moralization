# -*- coding: utf-8 -*-
import tkinter as tk

from experiment_game import (
    ExperimentGame,
    FIRE_SIZE,
    RIGHT_BG,
    SCORE_START,
    TIMER_SECONDS,
)


class LayoutTutorialGame(ExperimentGame):
    def __init__(self, root):
        super().__init__(root)

        self.root.title("Tutorial - Rozložení obrazovky")
        self.game_started = False
        self.game_over = False
        self.fires_paused = True
        self.tutorial_stage = -1

        self.score = SCORE_START
        self.time_left = TIMER_SECONDS
        self.score_label.config(text=self._format_score())
        self.timer_label.config(text=self._format_time(self.time_left))

        self.start_title_label.config(
            text="Tutorial - Rozložení obrazovky",
            fg="#2f5f8f",
        )
        self.start_hint_label.config(
            text=(
                "Stiskněte mezerník a rychle si projděte,\n"
                "kde během experimentu sledovat peníze a čas."
            ),
            font=("Trebuchet MS", 18, "bold"),
            fg="#4f3c2f",
        )

        self.guide_card = tk.Frame(
            self.root,
            bg="#fff7df",
            highlightbackground="#9b6b2f",
            highlightthickness=3,
            padx=26,
            pady=18,
        )
        self.guide_title_label = tk.Label(
            self.guide_card,
            text="",
            font=("Georgia", 22, "bold"),
            bg="#fff7df",
            fg="#2f5f8f",
            justify="center",
        )
        self.guide_title_label.pack(anchor="center")
        self.guide_body_label = tk.Label(
            self.guide_card,
            text="",
            font=("Trebuchet MS", 15, "bold"),
            bg="#fff7df",
            fg="#4f3c2f",
            justify="left",
            wraplength=860,
        )
        self.guide_body_label.pack(anchor="w", fill="x", pady=(12, 0))
        self.guide_hint_label = tk.Label(
            self.guide_card,
            text="",
            font=("Trebuchet MS", 14, "bold"),
            bg="#fff7df",
            fg="#8b2f17",
            justify="center",
            wraplength=860,
        )
        self.guide_hint_label.pack(anchor="center", pady=(14, 0))

        self.score_focus = tk.Frame(
            self.header,
            bg="#fff7df",
            highlightbackground="#c1121f",
            highlightthickness=4,
            bd=0,
        )
        self.score_focus.place_forget()
        self.score_focus_label = tk.Label(
            self.header,
            text="PENÍZE",
            font=("Trebuchet MS", 11, "bold"),
            bg="#fff7df",
            fg="#c1121f",
            padx=10,
            pady=2,
        )
        self.score_focus_label.place_forget()

        self.timer_focus = tk.Frame(
            self.header,
            bg="#eef7ff",
            highlightbackground="#2f78b2",
            highlightthickness=4,
            bd=0,
        )
        self.timer_focus.place_forget()
        self.timer_focus_label = tk.Label(
            self.header,
            text="ČAS",
            font=("Trebuchet MS", 11, "bold"),
            bg="#eef7ff",
            fg="#2f78b2",
            padx=10,
            pady=2,
        )
        self.timer_focus_label.place_forget()

        self.end_label.config(
            text="Layout máte hotový",
            font=("Georgia", 54, "bold"),
            fg="#2f5f8f",
        )
        self.end_message_label.config(
            text=(
                "Teď už jste viděli celou obrazovku experimentu.\n"
                "V další části už poběží běžná hra se ztrátou peněz i odpočtem času."
            ),
            font=("Trebuchet MS", 20, "bold"),
            fg="#4f3c2f",
            wraplength=1040,
        )
        self.end_hint_label = tk.Label(
            self.end_overlay,
            text="Enter = zkusit tutorial znovu, mezerník = ukončit tutorial",
            font=("Trebuchet MS", 16, "bold"),
            bg=RIGHT_BG,
            fg="#4f3c2f",
            justify="center",
            wraplength=1040,
        )
        self.end_hint_label.place(relx=0.5, rely=0.78, anchor="center")

        self.root.bind_all("<KeyPress-Return>", self.on_enter_press)
        self.root.bind_all("<KeyPress-KP_Enter>", self.on_enter_press)
        self.guide_card.bind("<Configure>", self._resize_guide_wraps)
        self.root.after(120, self._prepare_demo_layout)

    def _resize_guide_wraps(self, event=None):
        card_width = event.width if event is not None else self.guide_card.winfo_width()
        wraplength = max(700, min(900, card_width - 100))
        self.guide_body_label.config(wraplength=wraplength)
        self.guide_hint_label.config(wraplength=wraplength)

    def _prepare_demo_layout(self):
        self.left_canvas.update_idletasks()
        self.right_canvas.update_idletasks()
        width = self.left_canvas.winfo_width()
        height = self.left_canvas.winfo_height()
        if width <= 1 or height <= 1:
            self.root.after(100, self._prepare_demo_layout)
            return

        self.left_canvas.delete("bucket_cursor")
        self.left_canvas.delete("fire")
        self.active_fires.clear()
        self.fire_positions.clear()
        self.fire_counter = 0

        positions = (
            (0.28, 0.34),
            (0.68, 0.42),
            (0.54, 0.62),
        )
        for rel_x, rel_y in positions:
            self.fire_counter += 1
            tag = f"fire_{self.fire_counter}"
            x = int(width * rel_x)
            y = int(height * rel_y)
            self._draw_fire(x, y, FIRE_SIZE, tag)
            self.active_fires.add(tag)
            self.fire_positions[tag] = (x, y, FIRE_SIZE)

        self.left_canvas.tag_raise("fire")
        self._draw_right_scene()
        self._refresh_stage_view()

    def _draw_grass_background(self, event):
        ExperimentGame._draw_grass_background(self, event)
        self.left_canvas.delete("bucket_cursor")
        self.left_canvas.delete("tutorial_layout_left")
        if self.tutorial_stage == 0:
            self._draw_left_overview_badge()

    def _draw_right_scene(self, event=None):
        ExperimentGame._draw_right_scene(self, event)
        if not hasattr(self, "right_canvas"):
            return
        self.right_canvas.delete("tutorial_layout_right")
        if self.tutorial_stage == 0:
            self._draw_right_overview_badge()

    def _draw_left_overview_badge(self):
        width = self.left_canvas.winfo_width()
        if width <= 1:
            return
        x0 = max(22, int(width * 0.12))
        x1 = min(width - 22, int(width * 0.88))
        self.left_canvas.create_rectangle(
            x0,
            22,
            x1,
            92,
            fill="#fff7df",
            outline="#8b2f17",
            width=3,
            tags="tutorial_layout_left",
        )
        self.left_canvas.create_text(
            width * 0.5,
            45,
            text="LEVÁ STRANA",
            fill="#8b2f17",
            font=("Trebuchet MS", 15, "bold"),
            tags="tutorial_layout_left",
        )
        self.left_canvas.create_text(
            width * 0.5,
            70,
            text="Tady se objevují ohně a hasíte je kyblíkem.",
            fill="#4f3c2f",
            font=("Trebuchet MS", 13, "bold"),
            justify="center",
            width=max(200, x1 - x0 - 24),
            tags="tutorial_layout_left",
        )

    def _draw_right_overview_badge(self):
        width = self.right_canvas.winfo_width()
        if width <= 1:
            return
        x0 = max(22, int(width * 0.12))
        x1 = min(width - 22, int(width * 0.88))
        self.right_canvas.create_rectangle(
            x0,
            22,
            x1,
            92,
            fill="#fff7df",
            outline="#2f78b2",
            width=3,
            tags="tutorial_layout_right",
        )
        self.right_canvas.create_text(
            width * 0.5,
            45,
            text="PRAVÁ STRANA",
            fill="#2f78b2",
            font=("Trebuchet MS", 15, "bold"),
            tags="tutorial_layout_right",
        )
        self.right_canvas.create_text(
            width * 0.5,
            70,
            text="Tady ovládáte zavlažovací systém.",
            fill="#4f3c2f",
            font=("Trebuchet MS", 13, "bold"),
            justify="center",
            width=max(200, x1 - x0 - 24),
            tags="tutorial_layout_right",
        )

    def _refresh_stage_view(self):
        self.left_canvas.delete("tutorial_layout_left")
        self.right_canvas.delete("tutorial_layout_right")
        self.guide_card.place_forget()
        self.score_focus.place_forget()
        self.score_focus_label.place_forget()
        self.timer_focus.place_forget()
        self.timer_focus_label.place_forget()

        if self.tutorial_stage < 0:
            return

        self.guide_card.place(relx=0.5, rely=0.98, relwidth=0.76, anchor="s")
        self.guide_card.lift()

        if self.tutorial_stage == 0:
            self.guide_title_label.config(text="Tady už vidíte celou obrazovku experimentu")
            self.guide_body_label.config(
                text=(
                    "Obě varianty už máte vyzkoušené, takže tady jde jen o rychlou orientaci. "
                    "Vlevo se objevují ohně, vpravo ovládáte zavlažovací systém a nahoře "
                    "po celou dobu sledujete peníze a zbývající čas."
                )
            )
            self.guide_hint_label.config(
                text="Stiskněte mezerník a ukážeme si přesně, kde se odečítají peníze."
            )
            self._show_score_focus()
            self._show_timer_focus()
            self._draw_left_overview_badge()
            self._draw_right_overview_badge()
        elif self.tutorial_stage == 1:
            self.guide_title_label.config(text="Nahoře uprostřed vidíte, kolik peněz vám zbývá")
            self.guide_body_label.config(
                text=(
                    "Z této částky se průběžně odečítají ztráty. Za každý nový oheň zmizí 1,50 Kč. "
                    "Za každou sekundu, kdy oheň hoří, zmizí dalších 0,04 Kč za každý aktivní oheň. "
                    "Čím déle necháte oheň hořet, tím rychleji peníze klesají."
                )
            )
            self.guide_hint_label.config(
                text="Stiskněte mezerník a podíváme se na odpočet času."
            )
            self._show_score_focus()
        else:
            self.guide_title_label.config(text="Vpravo nahoře běží odpočet času")
            self.guide_body_label.config(
                text=(
                    "Tento čas ukazuje, kolik ještě zbývá do konce kola. "
                    "Jakmile odpočet doběhne na 00:00, hra okamžitě skončí, "
                    "i kdyby na ploše ještě zůstaly aktivní ohně."
                )
            )
            self.guide_hint_label.config(
                text="Stiskněte mezerník a tutorial ukončete."
            )
            self._show_timer_focus()

        self.score_label.lift()
        self.timer_label.lift()

    def _show_score_focus(self):
        self.score_focus.place(relx=0.5, rely=0.55, anchor="center", width=250, height=78)
        self.score_focus_label.place(relx=0.5, y=4, anchor="n")
        self.score_focus.lower(self.score_label)

    def _show_timer_focus(self):
        self.timer_focus.place(relx=0.935, rely=0.55, anchor="center", width=122, height=54)
        self.timer_focus_label.place(relx=0.935, y=4, anchor="n")
        self.timer_focus.lower(self.timer_label)

    def on_space_press(self, event=None):
        if self.end_overlay.winfo_ismapped():
            self.root.destroy()
            return

        if self.tutorial_stage == -1:
            self.tutorial_stage = 0
            self.start_overlay.place_forget()
            self._refresh_stage_view()
            return

        if self.tutorial_stage < 2:
            self.tutorial_stage += 1
            self._refresh_stage_view()
            return

        self.show_end_overlay()

    def on_enter_press(self, event=None):
        if self.end_overlay.winfo_ismapped():
            self.restart_tutorial()

    def restart_tutorial(self):
        self.game_over = False
        self.fires_paused = True
        self.tutorial_stage = -1
        self.end_overlay.place_forget()
        self.start_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.start_overlay.lift()
        self._refresh_stage_view()
        self._draw_right_scene()
        self.root.after(100, self._prepare_demo_layout)

    def show_end_overlay(self):
        self.guide_card.place_forget()
        self.score_focus.place_forget()
        self.score_focus_label.place_forget()
        self.timer_focus.place_forget()
        self.timer_focus_label.place_forget()
        self.left_canvas.delete("tutorial_layout_left")
        self.right_canvas.delete("tutorial_layout_right")
        self.end_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.end_overlay.lift()

    def schedule_next_fire(self):
        return

    def spawn_fire(self):
        return

    def update_score(self, delta):
        return

    def on_fire_tick(self):
        return

    def on_timer_tick(self):
        return

    def end_game(self):
        return

    def on_left_motion(self, event):
        self.left_canvas.delete("bucket_cursor")

    def on_left_leave(self, event):
        self.left_canvas.delete("bucket_cursor")

    def on_left_press(self, event):
        return

    def on_left_release(self, event):
        return

    def on_right_press(self, event):
        return

    def on_right_release(self, event):
        return

    def on_right_leave(self, event):
        return


if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutTutorialGame(root)
    root.mainloop()
