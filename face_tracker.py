from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp

from gesture_utils import eye_aspect_ratio, head_tilt_ratio, midpoint, mouth_open_ratio


LEFT_EYE_IDS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDS = [362, 385, 387, 263, 373, 380]


@dataclass
class FaceData:
    found: bool
    landmarks_px: list[tuple[int, int]]
    nose_norm: tuple[float, float] = (0.5, 0.5)
    left_ear: float = 0.0
    right_ear: float = 0.0
    mouth_ratio: float = 0.0
    head_tilt: float = 0.5
    both_eyes_closed: bool = False
    bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0)


class FaceTracker:
    def __init__(self) -> None:
        self._mp_face_mesh = mp.solutions.face_mesh
        self._mesh = self._mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
        )

    def process(self, frame_bgr) -> FaceData:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._mesh.process(frame_rgb)
        if not results.multi_face_landmarks:
            return FaceData(False, [])

        face_landmarks = results.multi_face_landmarks[0]
        height, width = frame_bgr.shape[:2]
        landmarks_px: list[tuple[int, int]] = []

        for landmark in face_landmarks.landmark:
            x_value = int(landmark.x * width)
            y_value = int(landmark.y * height)
            landmarks_px.append((x_value, y_value))

        x_values = [point[0] for point in landmarks_px]
        y_values = [point[1] for point in landmarks_px]
        bounding_box = self._square_box(
            x_min=min(x_values),
            y_min=min(y_values),
            x_max=max(x_values),
            y_max=max(y_values),
            frame_width=width,
            frame_height=height,
            padding_ratio=0.22,
        )

        left_eye_points = [landmarks_px[idx] for idx in LEFT_EYE_IDS]
        right_eye_points = [landmarks_px[idx] for idx in RIGHT_EYE_IDS]
        left_ear = eye_aspect_ratio(left_eye_points)
        right_ear = eye_aspect_ratio(right_eye_points)

        upper_lip = landmarks_px[13]
        lower_lip = landmarks_px[14]
        mouth_left = landmarks_px[61]
        mouth_right = landmarks_px[291]
        mouth_width = abs(mouth_right[0] - mouth_left[0])
        mouth_ratio = mouth_open_ratio(upper_lip, lower_lip, mouth_width)

        forehead = midpoint(landmarks_px[10], landmarks_px[151])
        nose = landmarks_px[1]
        chin = landmarks_px[152]
        head_tilt = head_tilt_ratio(nose, forehead, chin)

        cv2.rectangle(
            frame_bgr,
            (bounding_box[0], bounding_box[1]),
            (bounding_box[2], bounding_box[3]),
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame_bgr,
            "Face Tracking Zone",
            (bounding_box[0], max(25, bounding_box[1] - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
        )

        return FaceData(
            found=True,
            landmarks_px=landmarks_px,
            nose_norm=(face_landmarks.landmark[1].x, face_landmarks.landmark[1].y),
            left_ear=left_ear,
            right_ear=right_ear,
            mouth_ratio=mouth_ratio,
            head_tilt=head_tilt,
            both_eyes_closed=left_ear < 0.18 and right_ear < 0.18,
            bounding_box=bounding_box,
        )

    def close(self) -> None:
        self._mesh.close()

    @staticmethod
    def _square_box(
        x_min: int,
        y_min: int,
        x_max: int,
        y_max: int,
        frame_width: int,
        frame_height: int,
        padding_ratio: float,
    ) -> tuple[int, int, int, int]:
        box_width = x_max - x_min
        box_height = y_max - y_min
        side = int(max(box_width, box_height) * (1.0 + padding_ratio))
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        half_side = max(side // 2, 1)

        left = max(center_x - half_side, 0)
        top = max(center_y - half_side, 0)
        right = min(left + side, frame_width)
        bottom = min(top + side, frame_height)

        if right - left < side:
            left = max(right - side, 0)
        if bottom - top < side:
            top = max(bottom - side, 0)

        return left, top, right, bottom
