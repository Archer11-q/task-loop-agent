"""会话持久化：会话表 + 消息表（SQLite）

    存agent运行时状态，必须持久化，不受STORAGE开关印象，用独立库data/agent.db
"""
import json
import sqlite3
import uuid  # 生成随机字符串
from datetime import datetime
from pathlib import Path

from app.exceptions import SessionStorageError

BASE = Path(__file__).resolve().parent.parent.parent
SESSION_DB = BASE / "data" / "agent.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions(
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages(
    session_id  TEXT NOT NULL,
    seq         INTEGER NOT NULL,
    role        TEXT NOT NULL,
    payload     TEXT NOT NULL,
    PRIMARY KEY(session_id,seq)
);  
"""


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SessionStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or SESSION_DB
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.executescript(_SCHEMA)  # 一次性执行两次创建
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            raise SessionStorageError(f"会话库打开失败：{e}") from e

    def close(self) -> None:
        self.conn.close()

    # ---------- 会话 ----------
    def create_session(self, title: str) -> str:
        session_id = uuid.uuid4().hex
        now = _now()
        with self.conn:
            self.conn.execute(
                "INSERT INTO sessions(id,title,created_at,updated_at) VALUES(?,?,?,?)",
                (session_id, title, now, now),
            )
        return session_id

    def list_sessions(self, limit: int = 20) -> list[dict]:
        cur = self.conn.execute(
            """ SELECT s.id, s.title, s.updated_at, COUNT(m.seq) AS message_count
                FROM sessions s
                LEFT JOIN messages m ON m.session_id = s.id
                GROUP BY s.id, s.title, s.updated_at
                ORDER BY s.updated_at DESC LIMIT ? """, (limit,),
        )
        return [
            {"id": r[0], "title": r[1], "updated_at": r[2], "message_count": r[3]}
            for r in cur.fetchall()
        ]

    # ---------- 消息 ----------
    def load_messages(self, session_id: str) -> list[dict]:
        cur = self.conn.execute(
            "SELECT seq,payload FROM messages WHERE session_id=? ORDER BY seq",
            (session_id,),
        )
        return [json.loads(payload) for _, payload in cur.fetchall()]

    def replace_messages(self, session_id: str, messages: list[dict]) -> None:
        """全量覆盖，不是增量追加

        搭配DAY9的裁剪删掉消息，增量append无法表达删除，所以每次落库都是整份重写，当前代价可忽略
        """
        rows = [
            (session_id, i, m.get("role", ""), json.dumps(m, ensure_ascii=False))
            for i, m in enumerate(messages)
        ]

        try:
            with self.conn:
                self.conn.execute(
                    "DELETE FROM messages WHERE session_id=?", (session_id,)
                )
                self.conn.executemany(
                    "INSERT INTO messages(session_id,seq,role,payload) VALUES(?,?,?,?)",
                    rows,
                )
                self.conn.execute(
                    "UPDATE sessions SET updated_at=? WHERE id=?", (_now(), session_id)
                )
        except sqlite3.OperationalError as e:
            raise SessionStorageError(f"会话写入失败：{e}") from e
