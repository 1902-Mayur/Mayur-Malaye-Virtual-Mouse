from __future__ import annotations

import time

import pyautogui

from config import AppConfig
from gesture_utils import apply_dead_zone, clamp, exponential_smooth


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0


class MouseController:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.screen_width, self.screen_height = pyautogui.size()
        self.last_norm_point: tuple[float, float] | None = None
        self.smoothed_norm_point: tuple[float, float] | None = None
        self.dragging = False
        self.cursor_locked_until = 0.0

    def apply_actions(self, actions: list[dict], control_enabled: bool) -> None:
        for action in actions:
            action_type = action["type"]
            if action_type == "move_cursor" and control_enabled:
                self._move_cursor(action["point"])
            elif action_type == "left_click" and control_enabled:
                self.cursor_locked_until = time.time() + self.config.click_cursor_lock_seconds
                pyautogui.click(button="left")
            elif action_type == "right_click" and control_enabled:
                self.cursor_locked_until = time.time() + self.config.click_cursor_lock_seconds
                pyautogui.click(button="right")
            elif action_type == "double_click" and control_enabled:
                self.cursor_locked_until = time.time() + self.config.click_cursor_lock_seconds
                pyautogui.doubleClick()
            elif action_type == "scroll" and control_enabled:
                amount = int(self.config.sensitivities.scroll_speed * action.get("amount", 1.0))
                if action["direction"] == "down":
                    amount *= -1
                pyautogui.scroll(amount)
            elif action_type == "drag_start" and control_enabled and not self.dragging:
                pyautogui.mouseDown(button="left")
                self.dragging = True
            elif action_type == "drag_stop" and self.dragging:
                pyautogui.mouseUp(button="left")
                self.dragging = False
            elif action_type == "swipe" and control_enabled:
                if action["direction"] == "left":
                    pyautogui.hotkey("alt", "left")
                else:
                    pyautogui.hotkey("alt", "right")
            elif action_type == "copy" and control_enabled:
                pyautogui.hotkey("ctrl", "c")

    def _move_cursor(self, point: tuple[float, float]) -> None:
        if time.time() < self.cursor_locked_until:
            return

        if self.last_norm_point is None:
            self.last_norm_point = point

        filtered = apply_dead_zone(
            current_point=point,
            reference_point=self.last_norm_point,
            dead_zone=self.config.sensitivities.dead_zone,
        )
        self.last_norm_point = filtered
        self.smoothed_norm_point = exponential_smooth(
            current_value=filtered,
            previous_value=self.smoothed_norm_point,
            alpha=self.config.smoothing_factor,
        )

        speed = self.config.sensitivities.cursor_speed
        norm_x = clamp((self.smoothed_norm_point[0] - 0.5) * speed + 0.5, 0.0, 1.0)
        norm_y = clamp((self.smoothed_norm_point[1] - 0.5) * speed + 0.5, 0.0, 1.0)

        x_value = int(norm_x * self.screen_width)
        y_value = int(norm_y * self.screen_height)
        pyautogui.moveTo(x_value, y_value)
