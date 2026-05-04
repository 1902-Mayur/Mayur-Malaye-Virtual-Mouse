from __future__ import annotations

import time

import cv2

from config import DEFAULT_CONFIG, SensitivitySettings, UIState
from control_panel import ControlPanel
from database import DatabaseManager
from face_auth import extract_face_embedding, match_face_profile, save_face_image
from face_tracker import FaceTracker
from gesture_engine import GestureEngine
from hand_trackedr import HandTracker
from mouse_controller import MouseController
from profile_manager import ProfileManager


class VirtualMouseApp:
    def __init__(self) -> None:
        self.camera_window_x = 40
        self.camera_window_y = 40
        self.config = DEFAULT_CONFIG
        self.ui_state = UIState()
        self.database = DatabaseManager()
        self.database.initialize()
        self.profile_manager = ProfileManager(self.database)
        self.mouse_controller = MouseController(self.config)
        self.hand_tracker = HandTracker()
        self.face_tracker = FaceTracker()
        self.gesture_engine = GestureEngine(self.config, self.ui_state)
        self.panel = ControlPanel(
            config=self.config,
            ui_state=self.ui_state,
            on_mode_switch=self.toggle_mode,
            on_save_profile=self.save_current_profile,
            on_adjust_setting=self.adjust_setting,
        )
        self.capture = cv2.VideoCapture(self.config.camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
        self.latest_face_data = None
        self.latest_frame = None
        self.profile_loaded = False

    def toggle_mode(self) -> None:
        self.ui_state.mode = "face" if self.ui_state.mode == "hand" else "hand"
        self.ui_state.status_text = f"Mode changed to {self.ui_state.mode}"

    def adjust_setting(self, key: str, delta: float) -> None:
        settings = self.config.sensitivities
        current = getattr(settings, key)
        updated = current + delta
        if key in {"cursor_speed", "scroll_speed"}:
            updated = max(0.1, updated)
        elif key == "click_sensitivity":
            updated = min(max(0.02, updated), 0.35)
        elif key == "wink_sensitivity":
            updated = min(max(0.10, updated), 0.40)
        elif key == "dead_zone":
            updated = min(max(0.0, updated), 0.15)
        setattr(settings, key, round(updated, 3))
        self.ui_state.status_text = f"{key.replace('_', ' ').title()} set to {getattr(settings, key)}"

    def auto_load_profile(self) -> None:
        profiles = self.profile_manager.load_profiles()
        if not profiles:
            self.ui_state.status_text = "No saved profiles found. Using default settings."
            self.profile_loaded = True
            return

        started_at = time.time()
        while time.time() - started_at < self.config.auth_timeout_seconds:
            ok, frame = self.capture.read()
            if not ok:
                continue
            frame = cv2.flip(frame, 1)
            face_data = self.face_tracker.process(frame)
            self.latest_face_data = face_data
            self.latest_frame = frame.copy()
            if face_data.found:
                embedding = extract_face_embedding(frame, face_data.landmarks_px, face_data.bounding_box)
                matched_profile, score = match_face_profile(
                    embedding=embedding,
                    profiles=profiles,
                    threshold=self.config.face_match_threshold,
                )
                if matched_profile:
                    self._apply_profile(matched_profile)
                    self.ui_state.status_text = f"Loaded {matched_profile['name']} ({score:.2f})"
                    self.profile_loaded = True
                    return

            cv2.putText(
                frame,
                "Scanning face for profile...",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
            cv2.imshow(self.config.camera_window_name, frame)
            cv2.moveWindow(self.config.camera_window_name, self.camera_window_x, self.camera_window_y)
            self.panel.place_beside_camera(
                self.camera_window_x,
                self.camera_window_y,
                self.config.frame_width,
                self.config.frame_height,
            )
            self.panel.update()
            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.ui_state.status_text = "Profile not matched. Using default settings."
        self.profile_loaded = True

    def _apply_profile(self, profile: dict) -> None:
        self.config.sensitivities = SensitivitySettings.from_dict(profile["settings"])
        self.ui_state.active_profile = profile["name"]

    def save_current_profile(self) -> None:
        if self.latest_face_data is None or not self.latest_face_data.found or self.latest_frame is None:
            self.ui_state.status_text = "Face not detected. Cannot save profile."
            return

        name = self.profile_manager.next_profile_name()
        embedding = extract_face_embedding(
            self.latest_frame,
            self.latest_face_data.landmarks_px,
            self.latest_face_data.bounding_box,
        )
        image_path = self.profile_manager.ensure_profile_image_path(name)
        saved_image_path = save_face_image(self.latest_frame, self.latest_face_data.bounding_box, image_path)
        self.profile_manager.save_profile(
            name=name,
            face_image_path=saved_image_path,
            face_embedding=embedding,
            settings=self.config.sensitivities,
        )
        self.ui_state.active_profile = name
        self.ui_state.status_text = f"Profile saved as {name}"

    def overlay_status(self, frame) -> None:
        overlay = frame.copy()
        cv2.rectangle(overlay, (18, 18), (470, 155), (12, 20, 32), -1)
        cv2.rectangle(overlay, (18, 18), (470, 155), (0, 210, 255), 2)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        cv2.putText(
            frame,
            "VIRTUAL MOUSE",
            (34, 48),
            cv2.FONT_HERSHEY_DUPLEX,
            0.95,
            (245, 252, 255),
            2,
        )
        cv2.putText(
            frame,
            "Live gesture controller",
            (36, 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (110, 235, 210),
            2,
        )

        self._draw_info_line(frame, "MODE", self.ui_state.mode.upper(), 38, 104, (0, 210, 255))
        self._draw_info_line(frame, "PROFILE", self.ui_state.active_profile, 190, 104, (255, 214, 90))
        self._draw_info_line(frame, "STATUS", self.ui_state.status_text, 38, 134, (123, 245, 168))

        color = (0, 235, 120) if self.ui_state.control_enabled else (0, 70, 255)
        label = "ACTIVE" if self.ui_state.control_enabled else "PAUSED"
        cv2.circle(frame, (self.config.frame_width - 82, 48), 18, color, -1)
        cv2.circle(frame, (self.config.frame_width - 82, 48), 23, (255, 255, 255), 2)
        cv2.putText(
            frame,
            label,
            (self.config.frame_width - 148, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )

    @staticmethod
    def _draw_info_line(frame, label: str, value: str, x_value: int, y_value: int, value_color: tuple[int, int, int]) -> None:
        cv2.putText(
            frame,
            f"{label}:",
            (x_value, y_value),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.56,
            (188, 210, 230),
            2,
        )
        cv2.putText(
            frame,
            value,
            (x_value + 86, y_value),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.56,
            value_color,
            2,
        )

    def run(self) -> None:
        if not self.capture.isOpened():
            raise RuntimeError("Unable to open webcam.")

        self.auto_load_profile()

        while True:
            ok, frame = self.capture.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)
            self.latest_frame = frame.copy()
            hand_data = self.hand_tracker.process(frame)
            face_data = self.face_tracker.process(frame)
            self.latest_face_data = face_data

            actions = self.gesture_engine.update(hand_data, face_data)
            for action in actions:
                if action["type"] == "status":
                    self.ui_state.status_text = action["text"]

            self.mouse_controller.apply_actions(actions, self.ui_state.control_enabled)
            self.overlay_status(frame)
            cv2.imshow(self.config.camera_window_name, frame)
            cv2.moveWindow(self.config.camera_window_name, self.camera_window_x, self.camera_window_y)
            self.panel.place_beside_camera(
                self.camera_window_x,
                self.camera_window_y,
                self.config.frame_width,
                self.config.frame_height,
            )

            try:
                self.panel.update()
            except Exception:
                break

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break

        self.shutdown()

    def shutdown(self) -> None:
        self.hand_tracker.close()
        self.face_tracker.close()
        if self.capture:
            self.capture.release()
        cv2.destroyAllWindows()
        try:
            self.panel.close()
        except Exception:
            pass


if __name__ == "__main__":
    app = VirtualMouseApp()
    app.run()
