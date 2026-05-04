from __future__ import annotations

import math
import time
from collections import deque
from typing import Iterable


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    return math.dist(point_a, point_b)


def midpoint(point_a: tuple[float, float], point_b: tuple[float, float]) -> tuple[float, float]:
    return ((point_a[0] + point_b[0]) * 0.5, (point_a[1] + point_b[1]) * 0.5)


def normalize_landmarks(points: Iterable[tuple[float, float]], anchor: tuple[float, float], scale: float) -> list[float]:
    scale = max(scale, 1e-6)
    normalized = []
    for x_value, y_value in points:
        normalized.extend([(x_value - anchor[0]) / scale, (y_value - anchor[1]) / scale])
    return normalized


def apply_dead_zone(
    current_point: tuple[float, float],
    reference_point: tuple[float, float],
    dead_zone: float,
) -> tuple[float, float]:
    dx = current_point[0] - reference_point[0]
    dy = current_point[1] - reference_point[1]
    if math.hypot(dx, dy) < dead_zone:
        return reference_point
    return current_point


def exponential_smooth(
    current_value: tuple[float, float],
    previous_value: tuple[float, float] | None,
    alpha: float,
) -> tuple[float, float]:
    if previous_value is None:
        return current_value
    return (
        previous_value[0] + alpha * (current_value[0] - previous_value[0]),
        previous_value[1] + alpha * (current_value[1] - previous_value[1]),
    )


def eye_aspect_ratio(points: list[tuple[float, float]]) -> float:
    if len(points) != 6:
        return 0.0
    vertical_1 = distance(points[1], points[5])
    vertical_2 = distance(points[2], points[4])
    horizontal = distance(points[0], points[3])
    if horizontal == 0:
        return 0.0
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def mouth_open_ratio(upper_lip: tuple[float, float], lower_lip: tuple[float, float], mouth_width: float) -> float:
    if mouth_width <= 0:
        return 0.0
    return distance(upper_lip, lower_lip) / mouth_width


def head_tilt_ratio(nose: tuple[float, float], forehead: tuple[float, float], chin: tuple[float, float]) -> float:
    total = max(distance(forehead, chin), 1e-6)
    return (nose[1] - forehead[1]) / total


def fingers_up(landmarks: list[tuple[int, int]]) -> dict[str, bool]:
    if len(landmarks) < 21:
        return {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}

    return {
        "thumb": landmarks[4][0] > landmarks[3][0],
        "index": landmarks[8][1] < landmarks[6][1],
        "middle": landmarks[12][1] < landmarks[10][1],
        "ring": landmarks[16][1] < landmarks[14][1],
        "pinky": landmarks[20][1] < landmarks[18][1],
    }


class CooldownManager:
    def __init__(self) -> None:
        self._timestamps: dict[str, float] = {}

    def ready(self, key: str, cooldown: float) -> bool:
        now = time.time()
        previous = self._timestamps.get(key, 0.0)
        if now - previous >= cooldown:
            self._timestamps[key] = now
            return True
        return False


class MovementHistory:
    def __init__(self, maxlen: int = 6) -> None:
        self.points: deque[tuple[float, float]] = deque(maxlen=maxlen)

    def add(self, point: tuple[float, float]) -> None:
        self.points.append(point)

    def clear(self) -> None:
        self.points.clear()

    def swipe_direction(self, threshold: float = 0.12) -> str | None:
        if len(self.points) < 3:
            return None
        start = self.points[0]
        end = self.points[-1]
        delta_x = end[0] - start[0]
        delta_y = abs(end[1] - start[1])
        if abs(delta_x) < threshold or delta_y > abs(delta_x) * 0.6:
            return None
        return "right" if delta_x > 0 else "left"
