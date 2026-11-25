import json

from app.exceptions import TodoStorageCorruptError
from app.models import Todo, todo_to_dict
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

ADD_TODO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add_todo",
        "description": "新增一条待办。用户说“加一条待办”“记一下”“提醒我”时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "待办内容，保留用户原话里的时间与事项，如“明天开会”。",
                }
            },
            "required": ["content"],
        },
    },
}

DELETE_TODO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "delete_todo",
        "description": "删除一条待办，必须先调用 list_todos 拿到id 再删，不要猜id。",
        "parameters": {
            "type": "object",
            "properties": {
                "todo_id": {
                    "type": "integer",
                    "description": "待办编号，取 list_todos 返回结果里 todos[].id 的值",
                }
            },
            "required": ["todo_id"],
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


def add_todo(content: str) -> str:
    """新增一条待办，返回JSON字符串"""
    try:
        todos = STORE.load_todos()
        todos.append(Todo(content=content, is_done=False))
        STORE.save_todos(todos)
    except TodoStorageCorruptError as e:
        return json.dumps({"ok": False, "error": f"待办数据读写失败：{e}"}, ensure_ascii=False)

    return json.dumps({"ok": True, "id": len(todos) - 1, "content": content, "count": len(todos)}, ensure_ascii=False, )


def delete_todo(todo_id: int) -> str:
    """按列表下标删除一条待办，返回JSON字符串"""
    try:
        todos = STORE.load_todos()
        if todo_id < 0 or todo_id >= len(todos):
            return json.dumps(
                {"ok": False, "error": f"id {todo_id} 不存在，当前共 {len(todos)} 条待办"}, ensure_ascii=False,
            )
        removed = todos.pop(todo_id)
        STORE.save_todos(todos)
    except TodoStorageCorruptError as e:
        return json.dumps({"ok": False, "error": f"待办数据读写失败：{e}"}, ensure_ascii=False)

    return json.dumps({"ok": True, "deleted": removed.content, "count": len(todos)}, ensure_ascii=False, )
