"""工具层入口：注册表 + 分发"""

from .builtin_tools import (
    CALCULATE_SCHEMA,
    CURRENT_TIME_SCHEMA,
    calculate,
    current_time,
)
from .todo_tools import (
    ADD_TODO_SCHEMA,
    DELETE_TODO_SCHEMA,
    LIST_TODOS_SCHEMA,
    add_todo,
    delete_todo,
    list_todos,
)

# 模型看到的工具清单
TOOL_SCHEMA = [
    LIST_TODOS_SCHEMA,
    ADD_TODO_SCHEMA,
    DELETE_TODO_SCHEMA,
    CALCULATE_SCHEMA,
    CURRENT_TIME_SCHEMA
]

# 名字 -> 实现。加新工具只改这一张表和上面的 TOOL_SCHEMA
_HANDLERS = {
    "list_todos": list_todos,
    "add_todo": add_todo,
    "delete_todo": delete_todo,
    "calculate": calculate,
    "current_time": current_time,
}


def execute_tool(name: str, args: dict) -> str:
    """按名字分发到具体实现，永远返回字符串.

        未知工具/参数错误不抛异常：把错误文本交回模型，
        让模型决定是否重试、换工具还是直接回答
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return f"错误：未知工具 {name}，当前可用工具：{list(_HANDLERS)}"

    try:
        return handler(**args)
    except TypeError as e:
        # 模型少串/多传/类型错误，都会被 ** 解包拦下
        return f"错误：工具 {name} 的参数不匹配（{e}），收到的参数是 {args}"
