from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from config import DB_PATH, PROFILES_DIR


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    face_image_path TEXT NOT NULL,
                    face_embedding TEXT NOT NULL,
                    cursor_speed REAL NOT NULL,
                    click_sensitivity REAL NOT NULL,
                    scroll_speed REAL NOT NULL,
                    wink_sensitivity REAL NOT NULL,
                    dead_zone REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_profiles_updated_at
                AFTER UPDATE ON profiles
                BEGIN
                    UPDATE profiles
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = OLD.id;
                END
                """
            )
            conn.commit()

    def fetch_profiles(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, face_image_path, face_embedding, cursor_speed,
                       click_sensitivity, scroll_speed, wink_sensitivity, dead_zone
                FROM profiles
                ORDER BY name
                """
            ).fetchall()
        return [self._row_to_profile(row) for row in rows]

    def fetch_profile_by_name(self, name: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, face_image_path, face_embedding, cursor_speed,
                       click_sensitivity, scroll_speed, wink_sensitivity, dead_zone
                FROM profiles
                WHERE name = ?
                """,
                (name,),
            ).fetchone()
        return self._row_to_profile(row) if row else None

    def upsert_profile(
        self,
        name: str,
        face_image_path: str,
        face_embedding: list[float],
        settings: dict[str, float],
    ) -> None:
        payload = (
            name,
            face_image_path,
            json.dumps(face_embedding),
            float(settings["cursor_speed"]),
            float(settings["click_sensitivity"]),
            float(settings["scroll_speed"]),
            float(settings["wink_sensitivity"]),
            float(settings["dead_zone"]),
        )
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO profiles (
                    name,
                    face_image_path,
                    face_embedding,
                    cursor_speed,
                    click_sensitivity,
                    scroll_speed,
                    wink_sensitivity,
                    dead_zone
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    face_image_path = excluded.face_image_path,
                    face_embedding = excluded.face_embedding,
                    cursor_speed = excluded.cursor_speed,
                    click_sensitivity = excluded.click_sensitivity,
                    scroll_speed = excluded.scroll_speed,
                    wink_sensitivity = excluded.wink_sensitivity,
                    dead_zone = excluded.dead_zone
                """,
                payload,
            )
            conn.commit()

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "face_image_path": row["face_image_path"],
            "face_embedding": json.loads(row["face_embedding"]),
            "settings": {
                "cursor_speed": row["cursor_speed"],
                "click_sensitivity": row["click_sensitivity"],
                "scroll_speed": row["scroll_speed"],
                "wink_sensitivity": row["wink_sensitivity"],
                "dead_zone": row["dead_zone"],
            },
        }
