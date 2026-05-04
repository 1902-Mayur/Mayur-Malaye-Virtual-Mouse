from __future__ import annotations

import time

from config import AppConfig, UIState
from face_tracker import FaceData
from gesture_utils import CooldownManager, MovementHistory
from hand_trackedr import HandData


class GestureEngine:
    def __init__(self, config: AppConfig, ui_state: UIState) -> None:
        self.config = config
        self.ui_state = ui_state
        self.cooldowns = CooldownManager()
        self.hand_history = MovementHistory(maxlen=config.swipe_history_size)
        self.drag_anchor_time: float | None = None
        self.drag_active = False
        self.eye_close_started: float | None = None

    def update(self, hand_data: HandData, face_data: FaceData) -> list[dict]:
        actions: list[dict] = []

        if self.ui_state.mode == "hand":
            actions.extend(self._process_hand(hand_data))
        else:
            actions.extend(self._process_face(face_data))

        actions.extend(self._process_global(face_data))
        return actions

    def _process_hand(self, hand_data: HandData) -> list[dict]:
        actions: list[dict] = []
        if not hand_data.found:
            self.hand_history.clear()
            self.drag_anchor_time = None
            return actions

        self.hand_history.add(hand_data.palm_center_norm)
        finger_states = hand_data.finger_states

        if all(not state for state in finger_states.values()):
            if self.cooldowns.ready("pause", self.config.debounce_seconds["pause"]):
                self.ui_state.control_enabled = not self.ui_state.control_enabled
                status = "Gesture control resumed" if self.ui_state.control_enabled else "Gesture control paused"
                self.ui_state.status_text = status
                actions.append({"type": "status", "text": status})
            return actions

        if not self.ui_state.control_enabled:
            return actions

        click_threshold = max(self.config.sensitivities.click_sensitivity * 1.45, 0.06)
        left_pinch_active = hand_data.thumb_index_distance < click_threshold
        right_pinch_active = hand_data.thumb_middle_distance < click_threshold
        double_click_ready = hand_data.index_middle_distance < click_threshold * 1.05 and finger_states["thumb"]
        click_pose_active = left_pinch_active or right_pinch_active or double_click_ready

        if not click_pose_active or self.drag_active:
            actions.append({"type": "move_cursor", "source": "hand", "point": hand_data.index_tip_norm})

        if left_pinch_active and self.cooldowns.ready(
            "left_click", self.config.debounce_seconds["left_click"]
        ):
            actions.append({"type": "left_click"})

        if right_pinch_active and self.cooldowns.ready(
            "right_click", self.config.debounce_seconds["right_click"]
        ):
            actions.append({"type": "right_click"})

        if double_click_ready and self.cooldowns.ready("double_click", self.config.debounce_seconds["double_click"]):
            actions.append({"type": "double_click"})

        drag_threshold = max(self.config.sensitivities.click_sensitivity * 1.20, 0.055)
        if hand_data.thumb_index_distance < drag_threshold:
            if self.drag_anchor_time is None:
                self.drag_anchor_time = time.time()
            elif not self.drag_active and time.time() - self.drag_anchor_time >= self.config.drag_hold_seconds:
                self.drag_active = True
                actions.append({"type": "drag_start"})
        else:
            self.drag_anchor_time = None
            if self.drag_active:
                self.drag_active = False
                actions.append({"type": "drag_stop"})

        if finger_states["index"] and finger_states["middle"] and not finger_states["ring"] and not finger_states["pinky"]:
            if self.cooldowns.ready("scroll", self.config.debounce_seconds["scroll"]):
                actions.append({"type": "scroll", "direction": "up", "amount": 1.0})

        if not finger_states["index"] and not finger_states["middle"] and finger_states["ring"] and finger_states["pinky"]:
            if self.cooldowns.ready("scroll", self.config.debounce_seconds["scroll"]):
                actions.append({"type": "scroll", "direction": "down", "amount": 1.0})

        if finger_states["index"] and finger_states["middle"] and finger_states["ring"] and finger_states["pinky"]:
            direction = self.hand_history.swipe_direction()
            if direction and self.cooldowns.ready("swipe", self.config.debounce_seconds["swipe"]):
                actions.append({"type": "swipe", "direction": direction})
                self.hand_history.clear()

        if finger_states["thumb"] and finger_states["index"] and finger_states["middle"] and not finger_states["ring"] and finger_states["pinky"]:
            if self.cooldowns.ready("copy", self.config.debounce_seconds["copy"]):
                actions.append({"type": "copy"})

        return actions

    def _process_face(self, face_data: FaceData) -> list[dict]:
        actions: list[dict] = []
        if not face_data.found or not self.ui_state.control_enabled:
            return actions

        actions.append({"type": "move_cursor", "source": "face", "point": face_data.nose_norm})

        wink_threshold = self.config.sensitivities.wink_sensitivity
        left_wink = face_data.left_ear < wink_threshold and face_data.right_ear > face_data.left_ear + 0.035
        right_wink = face_data.right_ear < wink_threshold and face_data.left_ear > face_data.right_ear + 0.035

        if left_wink:
            if self.cooldowns.ready("left_click", self.config.debounce_seconds["left_click"]):
                actions.append({"type": "left_click"})

        if right_wink:
            if self.cooldowns.ready("right_click", self.config.debounce_seconds["right_click"]):
                actions.append({"type": "right_click"})

        if face_data.head_tilt < 0.42 and self.cooldowns.ready("scroll", self.config.debounce_seconds["scroll"]):
            actions.append({"type": "scroll", "direction": "up", "amount": 1.0})

        if face_data.head_tilt > 0.58 and self.cooldowns.ready("scroll", self.config.debounce_seconds["scroll"]):
            actions.append({"type": "scroll", "direction": "down", "amount": 1.0})

        if face_data.mouth_ratio > 0.22 and not self.drag_active:
            self.drag_active = True
            actions.append({"type": "drag_start"})
        elif face_data.mouth_ratio <= 0.18 and self.drag_active:
            self.drag_active = False
            actions.append({"type": "drag_stop"})

        return actions

    def _process_global(self, face_data: FaceData) -> list[dict]:
        actions: list[dict] = []
        if not face_data.found:
            self.eye_close_started = None
            return actions

        if face_data.both_eyes_closed:
            if self.eye_close_started is None:
                self.eye_close_started = time.time()
            elif time.time() - self.eye_close_started >= self.config.toggle_hold_seconds:
                if self.cooldowns.ready("mode_switch", self.config.debounce_seconds["mode_switch"]):
                    self.ui_state.mode = "face" if self.ui_state.mode == "hand" else "hand"
                    status = f"Mode changed to {self.ui_state.mode}"
                    self.ui_state.status_text = status
                    actions.append({"type": "status", "text": status})
                self.eye_close_started = None
        else:
            self.eye_close_started = None

        return actions
