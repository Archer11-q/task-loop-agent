from fastapi import FastAPI,HTTPException
from models import Todo,TodoCreate
from storage import get_storage
from exceptions import TodoStorageCorruptError

""" FastAPI 请求体"""
app = FastAPI(title="Todo API")
store = get_storage()

def todo_to_dict(t: Todo,idx: int):
    return {"id":idx,"content":t.content,"is_done":t.is_done}

@app.get("/todos")
def get_all():
    try:
        todo_list = store.load_todos()
        return [todo_to_dict(item, i) for i, item in enumerate(todo_list)]
    except TodoStorageCorruptError:
        raise HTTPException(status_code=500,detail="持久化数据损坏")

@app.post("/todos")
def create(req: TodoCreate):
    try:
        todo_list=store.load_todos()
        new_todo=Todo(content=req.content,is_done=False)
        todo_list.append(new_todo)
        store.save_todos(todo_list)
        return todo_to_dict(new_todo,len(todo_list)-1)
    except TodoStorageCorruptError:
        raise HTTPException(status_code=500,detail="持久化数据损坏")

@app.put("/todos/{todo_id}/done")
def mark_done(todo_id: int):
    try:
        todo_list=store.load_todos()
        if todo_id < 0 or todo_id >= len(todo_list):
            raise HTTPException(status_code=404,detail="待办不存在")
        todo_list[todo_id].is_done=True
        store.save_todos(todo_list)
        return todo_to_dict(todo_list[todo_id],todo_id)
    except TodoStorageCorruptError:
        raise HTTPException(status_code=500,detail="持久化数据损坏")

@app.delete("/todos/{todo_id}")
def delete(todo_id: int):
    try:
        todo_list=store.load_todos()
        if todo_id < 0 or todo_id >= len(todo_list):
            raise HTTPException(status_code=404,detail="待办不存在")
        todo_list.pop(todo_id)
        store.save_todos(todo_list)
        return {"message": f"id {todo_id} 删除成功"}
    except TodoStorageCorruptError:
        raise HTTPException(status_code=500, detail="持久化数据损坏")