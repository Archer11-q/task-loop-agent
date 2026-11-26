from .storage_json import StorageJson
from .storage_sqlite import StorageSqlite
from .storage_session import SessionStore     # 会话库，独立于 STORAGE_BACKEND
from app.config import STORAGE_BACKEND

"""
    不管底下用哪个后端，外面的代码（main.py、api.py）
    都只 from storage import get_storage 拿到统一入口
"""

def get_storage():
    if STORAGE_BACKEND == "sqlite":
        return StorageSqlite()
    return StorageJson()