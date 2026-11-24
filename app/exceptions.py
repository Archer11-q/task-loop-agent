"""存放异常类型"""

# 父子异常，统一接口
class TodoStorageCorruptError(Exception):
    pass

class TodoJsonCorruptError(TodoStorageCorruptError):
    """JSON文件损坏，子类"""
    pass

class TodoSqliteCorruptError(TodoStorageCorruptError):
    """SQLite数据库损坏，子类"""
    pass