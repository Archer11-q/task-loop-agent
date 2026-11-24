import pytest
from pathlib import Path
from unittest.mock import patch
from app.storage.storage_json import StorageJson
from app.storage.storage_sqlite import StorageSqlite
from app.exceptions import TodoJsonCorruptError, TodoSqliteCorruptError


# StorageJson测试
@pytest.fixture
def json_store(tmp_path: Path):
    test_file = tmp_path / "test.json"  # 测试隔离,不污染原有的数据
    with patch("app.storage.storage_json.TODO_FILE", test_file):
        store = StorageJson()
        yield store


def test_json_load_empty(json_store):
    """JSON: 文件不存在,load返回空列表"""
    res = json_store.load_todos()
    assert res == []


def test_json_corrupt_raise(tmp_path: Path):
    """JSON: 非法json格式,抛出TodoJsonCorruptError"""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{非法json", encoding="utf-8")
    with patch("app.storage.storage_json.TODO_FILE", bad_file):
        store = StorageJson()
        with pytest.raises(TodoJsonCorruptError):
            store.load_todos()


# StorageSqlite测试
@pytest.fixture
def sqlite_store(tmp_path: Path):
    db_file = tmp_path / "test.db"
    with patch("app.storage.storage_sqlite.DB_PATH",db_file):
        store = StorageSqlite()
        yield store
        store.conn.close()

def test_sqlite_load_empty(sqlite_store):
    res=sqlite_store.load_todos()
    assert res == []

def test_sqlite_corrupt_raise(tmp_path: Path):
    bad_file=tmp_path / "bad.db"
    bad_file.write_bytes(b"not valid sqlite")
    with patch("app.storage.storage_sqlite.DB_PATH",bad_file):
        with pytest.raises(TodoSqliteCorruptError):
            StorageSqlite()