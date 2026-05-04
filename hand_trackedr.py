from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp

from gesture_utils import distance, fingers_up


@dataclass
class HandData:
    found: bool
    landmarks_px: list[tuple[int, int]]
    landmarks_norm: list[tuple[float, float]]
    finger_states: dict[str, bool]
    thumb_index_distance: float = 1.0
    thumb_middle_distance: float = 1.0
    index_middle_distance: float = 1.0
    index_tip_norm: tuple[float, float] = (0.5, 0.5)
    palm_center_norm: tuple[float, float] = (0.5, 0.5)


class HandTracker:
    def __init__(self, max_num_hands: int = 1) -> None:
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self._drawer = mp.solutions.drawing_utils

    def process(self, frame_bgr) -> HandData:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._hands.process(frame_rgb)
        if not results.multi_hand_landmarks:
            return HandData(False, [], [], fingers_up([]))

        hand_landmarks = results.multi_hand_landmarks[0]
        height, width = frame_bgr.shape[:2]

        landmarks_px: list[tuple[int, int]] = []
        landmarks_norm: list[tuple[float, float]] = []
        for landmark in hand_landmarks.landmark:
            x_value = int(landmark.x * width)
            y_value = int(landmark.y * height)
            landmarks_px.append((x_value, y_value))
            landmarks_norm.append((landmark.x, landmark.y))

        self._drawer.draw_landmarks(
            frame_bgr,
            hand_landmarks,
            self._mp_hands.HAND_CONNECTIONS,
        )

        finger_states = fingers_up(landmarks_px)
        thumb_index_distance = distance(landmarks_norm[4], landmarks_norm[8])
        thumb_middle_distance = distance(landmarks_norm[4], landmarks_norm[12])
        index_middle_distance = distance(landmarks_norm[8], landmarks_norm[12])
        palm_points = [landmarks_norm[index] for index in (0, 5, 9, 13, 17)]
        palm_center_norm = (
            sum(point[0] for point in palm_points) / len(palm_points),
            sum(point[1] for point in palm_points) / len(palm_points),
        )

        return HandData(
            found=True,
            landmarks_px=landmarks_px,
            landmarks_norm=landmarks_norm,
            finger_states=finger_states,
            thumb_index_distance=thumb_index_distance,
            thumb_middle_distance=thumb_middle_distance,
            index_middle_distance=index_middle_distance,
            index_tip_norm=landmarks_norm[8],
            palm_center_norm=palm_center_norm,
        )

    def close(self) -> None:
        self._hands.close()
