"""Almacenamiento en SQLite: vídeos, canales y snapshots de estadísticas."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    channel_id TEXT,
    title TEXT,
    description TEXT,
    tags TEXT,
    category_id TEXT,
    published_at TEXT,
    duration_s INTEGER,
    is_short INTEGER,
    thumbnail TEXT,
    source TEXT,
    niche TEXT
);
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    title TEXT,
    subscribers INTEGER,
    video_count INTEGER,
    uploads_playlist TEXT,
    median_views REAL,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS snapshots (
    video_id TEXT,
    taken_at TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    PRIMARY KEY (video_id, taken_at)
);
"""


def connect(path: str | Path = "data/ytauto.db") -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_video(conn, v: dict) -> None:
    conn.execute(
        """INSERT INTO videos (id, channel_id, title, description, tags, category_id, published_at,
                               duration_s, is_short, thumbnail, source, niche)
           VALUES (:id, :channel_id, :title, :description, :tags, :category_id, :published_at,
                   :duration_s, :is_short, :thumbnail, :source, :niche)
           ON CONFLICT(id) DO UPDATE SET title=excluded.title,
               niche=COALESCE(videos.niche, excluded.niche)""",
        v,
    )


def add_snapshot(conn, video_id: str, taken_at: str, views: int, likes: int, comments: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO snapshots VALUES (?, ?, ?, ?, ?)",
        (video_id, taken_at, views, likes, comments),
    )


def upsert_channel(conn, c: dict) -> None:
    conn.execute(
        """INSERT INTO channels (id, title, subscribers, video_count, uploads_playlist, median_views, updated_at)
           VALUES (:id, :title, :subscribers, :video_count, :uploads_playlist, :median_views, :updated_at)
           ON CONFLICT(id) DO UPDATE SET title=excluded.title, subscribers=excluded.subscribers,
               video_count=excluded.video_count, uploads_playlist=excluded.uploads_playlist,
               median_views=COALESCE(excluded.median_views, channels.median_views),
               updated_at=excluded.updated_at""",
        c,
    )


def last_two_snapshots(conn, video_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM snapshots WHERE video_id=? ORDER BY taken_at DESC LIMIT 2", (video_id,)
    ).fetchall()
