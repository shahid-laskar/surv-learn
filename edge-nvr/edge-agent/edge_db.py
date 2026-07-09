"""SQLite persistence for edge NVR (motion, status, config cache, backup queue)."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = os.environ.get("EDGE_DB_PATH", "/data/edge.db")


def _db_path() -> str:
    url = os.environ.get("LOCAL_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "", 1)
    return DEFAULT_DB_PATH


@contextmanager
def connect():
    path = _db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS camera_config (
                cam_id TEXT PRIMARY KEY,
                cam_ip TEXT,
                cam_port INTEGER,
                onvif_port INTEGER,
                rtsp_url TEXT,
                onvif_username TEXT,
                onvif_password TEXT,
                motion_active INTEGER DEFAULT 0,
                retention_days INTEGER DEFAULT 30,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS motion_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cam_id TEXT NOT NULL,
                motion_start TEXT NOT NULL,
                motion_end TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                synced_to_hub INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS camera_status_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cam_id TEXT NOT NULL,
                is_online INTEGER NOT NULL,
                changed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS camera_online_state (
                cam_id TEXT PRIMARY KEY,
                is_online INTEGER NOT NULL,
                last_seen TEXT
            );

            CREATE TABLE IF NOT EXISTS pending_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cam_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                reason TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                uploaded INTEGER NOT NULL DEFAULT 0,
                object_key TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


def upsert_camera_configs(cameras: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        for c in cameras:
            conn.execute(
                """
                INSERT INTO camera_config (
                    cam_id, cam_ip, cam_port, onvif_port, rtsp_url,
                    onvif_username, onvif_password, motion_active, retention_days, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cam_id) DO UPDATE SET
                    cam_ip=excluded.cam_ip,
                    cam_port=excluded.cam_port,
                    onvif_port=excluded.onvif_port,
                    rtsp_url=excluded.rtsp_url,
                    onvif_username=excluded.onvif_username,
                    onvif_password=excluded.onvif_password,
                    motion_active=excluded.motion_active,
                    retention_days=excluded.retention_days,
                    updated_at=excluded.updated_at
                """,
                (
                    c["cam_id"],
                    c.get("cam_ip"),
                    c.get("cam_port") or 554,
                    c.get("onvif_port") or 80,
                    c.get("rtsp_url"),
                    c.get("onvif_username"),
                    c.get("onvif_password"),
                    1 if c.get("motion_active") else 0,
                    c.get("retention_days") or 30,
                    now,
                ),
            )


def list_camera_configs() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM camera_config").fetchall()
    return [dict(r) for r in rows]


def get_retention_by_cam() -> dict[str, int]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT cam_id, retention_days FROM camera_config"
        ).fetchall()
    return {r["cam_id"]: int(r["retention_days"] or 30) for r in rows}


def insert_motion_event(cam_id: str, motion_start: datetime, is_active: bool) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO motion_event (cam_id, motion_start, motion_end, is_active, synced_to_hub, created_at)
            VALUES (?, ?, NULL, ?, 0, ?)
            """,
            (cam_id, motion_start.isoformat(), 1 if is_active else 0, now),
        )
        return int(cur.lastrowid)


def close_motion_event(cam_id: str, motion_end: datetime) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE motion_event
            SET motion_end = ?, is_active = 0
            WHERE cam_id = ? AND is_active = 1 AND motion_end IS NULL
            """,
            (motion_end.isoformat(), cam_id),
        )


def fetch_unsynced_motion_events(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, cam_id, motion_start, motion_end, is_active
            FROM motion_event WHERE synced_to_hub = 0
            ORDER BY id LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def mark_motion_synced(event_id: int) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE motion_event SET synced_to_hub = 1 WHERE id = ?",
            (event_id,),
        )


def update_online_state(cam_id: str, is_online: bool) -> bool:
    """Returns True if state changed."""
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        row = conn.execute(
            "SELECT is_online FROM camera_online_state WHERE cam_id = ?",
            (cam_id,),
        ).fetchone()
        prev = bool(row["is_online"]) if row else None
        if prev is not None and prev == is_online:
            conn.execute(
                "UPDATE camera_online_state SET last_seen = ? WHERE cam_id = ?",
                (now, cam_id),
            )
            return False
        conn.execute(
            """
            INSERT INTO camera_online_state (cam_id, is_online, last_seen)
            VALUES (?, ?, ?)
            ON CONFLICT(cam_id) DO UPDATE SET
                is_online=excluded.is_online,
                last_seen=excluded.last_seen
            """,
            (cam_id, 1 if is_online else 0, now),
        )
        conn.execute(
            """
            INSERT INTO camera_status_log (cam_id, is_online, changed_at)
            VALUES (?, ?, ?)
            """,
            (cam_id, 1 if is_online else 0, now),
        )
        return True


def queue_backup(cam_id: str, file_path: str, reason: str, captured_at: datetime) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO pending_backup (cam_id, file_path, reason, captured_at, uploaded)
            VALUES (?, ?, ?, ?, 0)
            """,
            (cam_id, file_path, reason, captured_at.isoformat()),
        )


def fetch_pending_backups(limit: int = 10) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, cam_id, file_path, reason, captured_at
            FROM pending_backup WHERE uploaded = 0
            ORDER BY id LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def mark_backup_uploaded(backup_id: int, object_key: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE pending_backup SET uploaded = 1, object_key = ? WHERE id = ?
            """,
            (object_key, backup_id),
        )


def set_meta(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_meta (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def get_meta(key: str) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM agent_meta WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else None
