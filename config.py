from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROFILES_DIR = DATA_DIR / "profiles"
DB_PATH = DATA_DIR / "virtual_mouse.db"


@dataclass
class SensitivitySettings:
    cursor_speed: float = 1.0
    click_sensitivity: float = 0.08
    scroll_speed: float = 120.0
    wink_sensitivity: float = 0.22
    dead_zone: float = 0.025

    def as_dict(self) -> dict:
        return {
            "cursor_speed": self.cursor_speed,
            "click_sensitivity": self.click_sensitivity,
            "scroll_speed": self.scroll_speed,
            "wink_sensitivity": self.wink_sensitivity,
            "dead_zone": self.dead_zone,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "SensitivitySettings":
        payload = payload or {}
        return cls(
            cursor_speed=float(payload.get("cursor_speed", 1.0)),
            click_sensitivity=float(payload.get("click_sensitivity", 0.08)),
            scroll_speed=float(payload.get("scroll_speed", 120.0)),
            wink_sensitivity=float(payload.get("wink_sensitivity", 0.22)),
            dead_zone=float(payload.get("dead_zone", 0.025)),
        )


@dataclass
class UIState:
    mode: str = "hand"
    control_enabled: bool = True
    active_profile: str = "Guest"
    status_text: str = "Ready"


@dataclass
class AppConfig:
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    camera_window_name: str = "Virtual Mouse Camera"
    smoothing_factor: float = 0.35
    click_cursor_lock_seconds: float = 0.16
    auth_timeout_seconds: float = 3.5
    swipe_history_size: int = 6
    face_match_threshold: float = 0.86
    drag_hold_seconds: float = 0.45
    toggle_hold_seconds: float = 0.35
    double_click_gap: float = 0.40
    debounce_seconds: dict = field(
        default_factory=lambda: {
            "left_click": 0.35,
            "right_click": 0.35,
            "double_click": 0.55,
            "copy": 0.65,
            "scroll": 0.08,
            "swipe": 0.50,
            "mode_switch": 0.80,
            "pause": 0.80,
            "drag": 0.25,
        }
    )
    sensitivities: SensitivitySettings = field(default_factory=SensitivitySettings)


DEFAULT_CONFIG = AppConfig()
