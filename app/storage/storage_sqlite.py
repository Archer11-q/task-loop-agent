import sqlite3
import threading
from pathlib import Path
from models import Todo
from exceptions import TodoSqliteCorruptError

""" 数据Sqlite持久化"""

# 数据库文件名
DB_PATH = Path(__file__).resolve().parent.parent / "todo.db"


class StorageSqlite:
    def __init__(self):
        self.conn=sqlite3.connect(DB_PATH,check_same_thread=False)
        self.lock = threading.Lock()
        self._init_table()

    def _init_table(self):
        cur=self.conn.cursor()      # 从连接中取出游标
        cur.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                is_done INTEGER NOT NULL DEFAULT 0
            )
        """)

    def load_todos(self) -> list[Todo]:
        with self.lock:
            try:
                cur=self.conn.cursor()
                cur.execute("SELECT content,is_done FROM todos ORDER BY id")
                rows=cur.fetchall()
                return [Todo(content=r[0],is_done=bool(r[1])) for r in rows]
            except sqlite3.DatabaseError as e:
                raise TodoSqliteCorruptError("sqlite数据损坏，读取失败") from e

    def save_todos(self,todos: list[Todo]):
        with self.lock:
            try:
                cur=self.conn.cursor()
                cur.execute("DELETE FROM todos")
                for t in todos:
                    cur.execute("INSERT INTO todos(content,is_done) VALUES(?,?)",(t.content,int(t.is_done)))
                self.conn.commit()
            except sqlite3.DatabaseError as e:
                raise TodoSqliteCorruptError("sqlite写入数据损坏") from e