from __future__ import annotations

from pathlib import Path

from config import PROFILES_DIR, SensitivitySettings
from database import DatabaseManager


class ProfileManager:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def load_profiles(self) -> list[dict]:
        return self.database.fetch_profiles()

    def load_profile(self, name: str) -> dict | None:
        return self.database.fetch_profile_by_name(name)

    def save_profile(
        self,
        name: str,
        face_image_path: str,
        face_embedding: list[float],
        settings: SensitivitySettings,
    ) -> None:
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        self.database.upsert_profile(
            name=name,
            face_image_path=face_image_path,
            face_embedding=face_embedding,
            settings=settings.as_dict(),
        )

    def next_profile_name(self) -> str:
        existing = {profile["name"] for profile in self.load_profiles()}
        counter = 1
        while True:
            candidate = f"User {counter}"
            if candidate not in existing:
                return candidate
            counter += 1

    def ensure_profile_image_path(self, name: str) -> Path:
        safe_name = "".join(char if char.isalnum() else "_" for char in name).strip("_") or "user"
        return PROFILES_DIR / f"{safe_name}.png"
