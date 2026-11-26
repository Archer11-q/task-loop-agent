"""tests 共用夹具：内存表storage、脚本话的假chat"""
import pytest

from app.exceptions import TodoStorageCorruptError


class FakeStore:
    """内存版 storage，替掉真实文件/SQLite，测试不碰 data/。"""

    def __init__(self, todos=None):
        self.todos = list(todos or [])

    def load_todos(self):
        return list(self.todos)

    def save_todos(self, todos):
        self.todos = list(todos)


class BrokenStore:
    """任何读写都抛存储异常，用来测工具层的兜底"""

    def load_todos(self):
        raise TodoStorageCorruptError("模拟损坏")

    def save_todos(self, todos):
        raise TodoStorageCorruptError("模拟损坏")


@pytest.fixture
def fake_store():
    return FakeStore()


@pytest.fixture
def todo_store(fake_store, monkeypatch):
    """把 todo_tools里的模板级 STORE 换成内存版"""
    from app.tools import todo_tools

    monkeypatch.setattr(todo_tools, "STORE", fake_store)
    return fake_store


@pytest.fixture
def broken_todo_store(monkeypatch):
    from app.tools import todo_tools

    monkeypatch.setattr(todo_tools, "STORE", BrokenStore())
