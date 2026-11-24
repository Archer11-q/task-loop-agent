from app.storage import get_storage
from app.exceptions import TodoStorageCorruptError
from app.models import Todo

"""
    CLI 命令业务逻辑层：处理 add/list/finish/del 四条指令的实际执行
"""

store = get_storage()


def _add(content: str):
    todos: list = store.load_todos()
    todos.append(Todo(content, False))
    store.save_todos(todos)
    print(f"已添加：{content}")


def _list(show_done_only: bool):
    todos: list = store.load_todos()
    if not todos:
        print("暂无待办")
        return
    for idx, t in enumerate(todos):
        if show_done_only and not t.is_done:
            continue
        status = "[已完成] " if t.is_done else "[未完成]"
        print(f"[{idx}] {status} {t.content}")


def _finish(todo_id: int):
    todos: list = store.load_todos()
    if 0 <= todo_id < len(todos):
        todos[todo_id].is_done = True
        store.save_todos(todos)
        print(f"[已完成] {todos[todo_id].content}")
    else:
        print(f"未找到该待办: {todo_id}")


def _delete(todo_id: int):
    todos: list = store.load_todos()
    if 0 <= todo_id < len(todos):
        items = todos[todo_id]
        todos.pop(todo_id)
        store.save_todos(todos)
        print(f"[已删除] {items.content}")
    else:
        print(f"未找到该待办: {todo_id}")


def run(args):
    """对外唯一入口: 接收解析后的参数,分发指令,统一捕获异常"""
    try:
        if args.cmd == "add":
            _add(args.content)
        elif args.cmd == "list":
            _list(args.done)
        elif args.cmd == "finish":
            _finish(args.id)
        elif args.cmd == "del":
            _delete(args.id)
    except TodoStorageCorruptError:
        print("错误：待办文件损坏")
