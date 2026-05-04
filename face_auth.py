from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from config import PROFILES_DIR
from gesture_utils import normalize_landmarks


EMBEDDING_LANDMARK_IDS = [1, 4, 33, 61, 133, 152, 263, 291]


def extract_face_embedding(
    frame_bgr: np.ndarray,
    landmarks_px: list[tuple[int, int]],
    bounding_box: tuple[int, int, int, int],
) -> list[float]:
    if len(landmarks_px) <= max(EMBEDDING_LANDMARK_IDS):
        return []

    nose = landmarks_px[1]
    left_eye = landmarks_px[33]
    right_eye = landmarks_px[263]
    scale = math.dist(left_eye, right_eye)
    selected_points = [landmarks_px[idx] for idx in EMBEDDING_LANDMARK_IDS]
    geometry = normalize_landmarks(selected_points, anchor=nose, scale=scale)

    x_min, y_min, x_max, y_max = bounding_box
    face_crop = frame_bgr[max(y_min, 0):max(y_max, 0), max(x_min, 0):max(x_max, 0)]
    if face_crop.size == 0:
        appearance = [0.0] * 64
    else:
        face_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        face_small = cv2.resize(face_gray, (8, 8), interpolation=cv2.INTER_AREA)
        appearance = (face_small.flatten() / 255.0).tolist()

    return geometry + appearance


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    a = np.array(vector_a, dtype=np.float32)
    b = np.array(vector_b, dtype=np.float32)
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)


def match_face_profile(
    embedding: list[float],
    profiles: list[dict],
    threshold: float,
) -> tuple[dict | None, float]:
    best_profile = None
    best_score = 0.0
    for profile in profiles:
        score = cosine_similarity(embedding, profile["face_embedding"])
        if score > best_score:
            best_score = score
            best_profile = profile
    if best_score >= threshold:
        return best_profile, best_score
    return None, best_score


def save_face_image(frame_bgr: np.ndarray, bounding_box: tuple[int, int, int, int], output_path: Path) -> str:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    x_min, y_min, x_max, y_max = bounding_box
    face_crop = frame_bgr[max(y_min, 0):max(y_max, 0), max(x_min, 0):max(x_max, 0)]
    if face_crop.size == 0:
        face_crop = frame_bgr.copy()
    else:
        face_crop = cv2.resize(face_crop, (240, 240), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(output_path), face_crop)
    return str(output_path)
