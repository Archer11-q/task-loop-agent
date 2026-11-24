import json

from app.exceptions import TodoStorageCorruptError
from app.models import todo_to_dict
from app.storage import get_storage

""" 待办工具的 schema 与实现"""

# 模块顶层只取一次：StorageSqlite 每次实例化都会新开一个连接
STORE = get_storage()

# 模型只靠 description 决定调不调
LIST_TODOS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_todos",
        "description": (
            "查询当前所有待办事项，返回待办总数，以及每一条的内容和完成状态。"
            "当用户问“我有几条待办”“还有什么事没做”“列一下待办”时调用。"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def list_todos() -> str:
    """工具实现：返回JSON字符串"""
    try:
        todos = STORE.load_todos()
    except TodoStorageCorruptError as e:
        # 工具失败也返回字符串，让模型知道发生了什么，避免把循环停掉
        return json.dumps({"error": f"待办数据读取失败：{e}"}, ensure_ascii=False)

    payload = {
        "count": len(todos),
        "todos": [todo_to_dict(t, i) for i, t in enumerate(todos)]
    }
    return json.dumps(payload, ensure_ascii=False)
