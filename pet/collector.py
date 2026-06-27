
"""Codex 数据采集器 — 从本地 SQLite 数据库读取 Token 用量。"""

from __future__ import annotations

import sqlite3
import os
from dataclasses import dataclass


CODEX_DB_PATH = os.path.join(
    os.environ.get("USERPROFILE", "C:\\Users\\default"),
    ".codex",
    "state_5.sqlite",
)


@dataclass
class CollectorResult:
    total_tokens: int
    active_thread_count: int
    latest_thread_title: str
    latest_thread_tokens: int
    error: str = ""


class CodexCollector:
    """定时轮询 Codex 数据库获取用量信息。"""

    def __init__(self, db_path: str = CODEX_DB_PATH):
        self._db_path = db_path
        self._last_total: int | None = None

    def collect(self) -> CollectorResult:
        """读取数据库，返回当前用量快照。"""
        if not os.path.exists(self._db_path):
            return CollectorResult(
                total_tokens=0,
                active_thread_count=0,
                latest_thread_title="",
                latest_thread_tokens=0,
                error=f"数据库不存在: {self._db_path}",
            )

        try:
            conn = sqlite3.connect(self._db_path, timeout=1)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # 全部活跃线程的总和
            cur.execute(
                "SELECT COALESCE(SUM(tokens_used), 0) AS total, COUNT(*) AS cnt "
                "FROM threads WHERE archived = 0"
            )
            row = cur.fetchone()
            total = row["total"]
            count = row["cnt"]

            # 最近活跃的线程
            cur.execute(
                "SELECT title, tokens_used FROM threads "
                "WHERE archived = 0 ORDER BY updated_at DESC, updated_at_ms DESC LIMIT 1"
            )
            latest = cur.fetchone()
            latest_title = str(latest["title"] or "") if latest else ""
            latest_tokens = int(latest["tokens_used"]) if latest else 0

            conn.close()

            self._last_total = total

            return CollectorResult(
                total_tokens=int(total),
                active_thread_count=int(count),
                latest_thread_title=latest_title,
                latest_thread_tokens=int(latest_tokens),
            )

        except sqlite3.Error as e:
            return CollectorResult(
                total_tokens=self._last_total or 0,
                active_thread_count=0,
                latest_thread_title="",
                latest_thread_tokens=0,
                error=str(e),
            )
