from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class Todo:
    content: str
    is_done: bool = False


# FastAPI请求体
class TodoCreate(BaseModel):
    content: str


# 序列化：todo的list字段转为dict字段
def todo_to_dict(todo: "Todo", idx: int) -> dict:
    """统一的对外表示：id 用列表下标（CLI / API / 工具三处保持一致）"""
    return {"id": idx, "content": todo.content, "is_done": todo.is_done}
