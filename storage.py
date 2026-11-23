import json
from models import Todo

""" 数据json持久化存储"""

# 文件名称常量
TODO_FILE="todo.json"

# 自定义异常
class TodoJsonCorruptError(Exception):
    pass


# 加载函数：将文件内容加载到json
def load_todos() -> list[Todo]:
    try:
        with open(TODO_FILE,"r",encoding="utf-8") as f:
            raw = json.load(f)
        return [Todo(content=item[0],is_done=item[1]) for item in raw]
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        raise TodoJsonCorruptError("JSON文件损坏")

# 保存函数：执行增删改操作时修改文件
def save_todos(todos: list[Todo]):
    raw=[[t.content,t.is_done] for t in todos]
    with open(TODO_FILE,"w",encoding="utf-8") as f:
        json.dump(raw,f,ensure_ascii=False,indent=2)   # 防止中文乱码，进行格式化