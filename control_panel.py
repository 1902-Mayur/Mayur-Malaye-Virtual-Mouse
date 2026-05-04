from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config import AppConfig, UIState


class ControlPanel:
    def __init__(
        self,
        config: AppConfig,
        ui_state: UIState,
        on_mode_switch,
        on_save_profile,
        on_adjust_setting,
    ) -> None:
        self.config = config
        self.ui_state = ui_state
        self.on_mode_switch = on_mode_switch
        self.on_save_profile = on_save_profile
        self.on_adjust_setting = on_adjust_setting

        self.root = tk.Tk()
        self.root.title("Virtual Mouse Control Panel")
        self.root.geometry("520x720+1320+40")
        self.root.resizable(False, False)
        self.root.configure(bg="#101820")

        self.status_var = tk.StringVar(value="Status: Ready")
        self.mode_var = tk.StringVar(value="Mode: hand")
        self.profile_var = tk.StringVar(value="Profile: Guest")
        self.settings_vars: dict[str, tk.StringVar] = {}

        self._build_styles()

        self._build()

    def _build_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Panel.TFrame", background="#101820")
        style.configure("Card.TFrame", background="#172635")
        style.configure("InfoTitle.TLabel", background="#101820", foreground="#9adcfb", font=("Segoe UI", 10, "bold"))
        style.configure("Hero.TLabel", background="#101820", foreground="#f7fbff", font=("Segoe UI", 20, "bold"))
        style.configure("SubHero.TLabel", background="#101820", foreground="#6ee7c8", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#172635", foreground="#fef3c7", font=("Segoe UI", 11, "bold"))
        style.configure("CardText.TLabel", background="#172635", foreground="#ecfdf5", font=("Segoe UI", 10))
        style.configure("Value.TLabel", background="#172635", foreground="#8be9fd", font=("Segoe UI", 10, "bold"))
        style.configure("RowLabel.TLabel", background="#172635", foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        style.configure(
            "Accent.TButton",
            background="#00c2ff",
            foreground="#08121a",
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map("Accent.TButton", background=[("active", "#3bffb6")], foreground=[("active", "#041016")])
        style.configure(
            "Warm.TButton",
            background="#ff8a00",
            foreground="#1a0d00",
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map("Warm.TButton", background=[("active", "#ffd166")], foreground=[("active", "#261400")])
        style.configure(
            "Decrease.TButton",
            background="#ff5f6d",
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map("Decrease.TButton", background=[("active", "#ff8c94")], foreground=[("active", "#ffffff")])
        style.configure(
            "Increase.TButton",
            background="#00d084",
            foreground="#041016",
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map("Increase.TButton", background=[("active", "#7cf7c4")], foreground=[("active", "#041016")])

    def _build(self) -> None:
        outer_wrapper = ttk.Frame(self.root, style="Panel.TFrame")
        outer_wrapper.pack(fill=tk.BOTH, expand=True)

        dock_strip = tk.Frame(outer_wrapper, bg="#00d4ff", width=8)
        dock_strip.pack(side=tk.LEFT, fill=tk.Y)

        canvas = tk.Canvas(
            outer_wrapper,
            bg="#101820",
            highlightthickness=0,
            bd=0,
        )
        scrollbar = ttk.Scrollbar(outer_wrapper, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        wrapper = ttk.Frame(canvas, padding=18, style="Panel.TFrame")
        self._canvas_window = canvas.create_window((0, 0), window=wrapper, anchor="nw")
        self._scroll_canvas = canvas

        wrapper.bind("<Configure>", self._on_content_configure)
        canvas.bind("<Configure>", self._on_canvas_configure)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

        title = ttk.Label(wrapper, text="Virtual Mouse", style="Hero.TLabel")
        title.pack(anchor=tk.W)
        subtitle = ttk.Label(
            wrapper,
            text="Real-time hand and face gesture controller",
            style="SubHero.TLabel",
        )
        subtitle.pack(anchor=tk.W, pady=(4, 16))

        info_frame = ttk.Frame(wrapper, padding=14, style="Card.TFrame")
        info_frame.pack(fill=tk.X, pady=(0, 14))
        ttk.Label(info_frame, text="SESSION", style="InfoTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(info_frame, textvariable=self.mode_var, style="CardTitle.TLabel").pack(anchor=tk.W, pady=(8, 0))
        ttk.Label(info_frame, textvariable=self.profile_var, style="CardText.TLabel").pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(info_frame, textvariable=self.status_var, style="CardText.TLabel", wraplength=370).pack(anchor=tk.W, pady=(6, 0))

        button_frame = ttk.Frame(wrapper, style="Panel.TFrame")
        button_frame.pack(fill=tk.X, pady=(0, 14))
        ttk.Button(button_frame, text="Switch Mode", command=self.on_mode_switch, style="Accent.TButton").grid(
            row=0, column=0, padx=(0, 8), pady=4, sticky="ew"
        )
        ttk.Button(button_frame, text="Save Profile", command=self.on_save_profile, style="Warm.TButton").grid(
            row=0, column=1, padx=(8, 0), pady=4, sticky="ew"
        )
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        settings_frame = ttk.Frame(wrapper, padding=14, style="Card.TFrame")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(settings_frame, text="SENSITIVITY CONTROLS", style="InfoTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10)
        )

        controls = [
            ("Cursor Speed", "cursor_speed", 0.1),
            ("Click Sensitivity", "click_sensitivity", 0.01),
            ("Scroll Speed", "scroll_speed", 10.0),
            ("Wink Sensitivity", "wink_sensitivity", 0.01),
            ("Dead Zone", "dead_zone", 0.005),
        ]

        for row_index, (label, key, step) in enumerate(controls, start=1):
            value_var = tk.StringVar()
            self.settings_vars[key] = value_var
            ttk.Label(settings_frame, text=label, style="RowLabel.TLabel").grid(
                row=row_index, column=0, sticky=tk.W, padx=6, pady=12
            )
            ttk.Label(settings_frame, textvariable=value_var, style="Value.TLabel", width=8).grid(
                row=row_index, column=1, sticky=tk.W, padx=8
            )
            ttk.Button(
                settings_frame,
                text="Decrease",
                width=10,
                style="Decrease.TButton",
                command=lambda setting=key, delta=-step: self.on_adjust_setting(setting, delta),
            ).grid(row=row_index, column=2, padx=6, sticky="ew")
            ttk.Button(
                settings_frame,
                text="Increase",
                width=10,
                style="Increase.TButton",
                command=lambda setting=key, delta=step: self.on_adjust_setting(setting, delta),
            ).grid(row=row_index, column=3, padx=6, sticky="ew")

        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(2, weight=1)
        settings_frame.grid_columnconfigure(3, weight=1)

    def update(self) -> None:
        self.mode_var.set(f"Mode: {self.ui_state.mode}")
        self.profile_var.set(f"Profile: {self.ui_state.active_profile}")
        self.status_var.set(f"Status: {self.ui_state.status_text}")
        sensitivities = self.config.sensitivities
        for key, variable in self.settings_vars.items():
            variable.set(f"{getattr(sensitivities, key):.3f}")
        self.root.update_idletasks()
        self.root.update()

    def place_beside_camera(self, camera_x: int, camera_y: int, camera_width: int, camera_height: int) -> None:
        panel_x = camera_x + camera_width
        panel_y = camera_y
        panel_height = max(camera_height, 560)
        self.root.geometry(f"520x{panel_height}+{panel_x}+{panel_y}")

    def close(self) -> None:
        self.root.unbind_all("<MouseWheel>")
        self.root.destroy()

    def _on_content_configure(self, event) -> None:
        self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._scroll_canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
