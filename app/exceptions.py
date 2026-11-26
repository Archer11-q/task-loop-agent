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


class AgentError(Exception):
    """agent循环层异常基类"""
    pass


class AgentMaxTurnsError(AgentError):
    """达到最大轮数仍未首位：模型反复调工具，或工具一直失败"""
    pass


class SessionStorageError(Exception):
    """会话/消息持久化失败"""
