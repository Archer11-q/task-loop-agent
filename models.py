from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class Todo:
    content:str
    is_done:bool=False

# FastAPI请求体
class TodoCreate(BaseModel):
    content:str