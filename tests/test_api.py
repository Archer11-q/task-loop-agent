import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_storage():
    """每条用例执行前清空数据"""
    from app.storage import get_storage
    storage = get_storage()
    storage.save_todos([])  # 测试跑前清理
    yield
    storage.save_todos([])  # 测试跑后清理


# 正常场景:增删改查
def test_create_todo():
    resp = client.post("/todos", json={"content": "学习pytest"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 0
    assert data["content"] == "学习pytest"
    assert data["is_done"] is False


def test_get_all():
    client.post("/todos", json={"content": "任务A"})
    client.post("/todos", json={"content": "任务B"})
    resp = client.get("/todos")
    assert resp.status_code == 200
    todo_list = resp.json()
    assert len(todo_list) == 2


def test_mark_done():
    client.post("/todos", json={"content": "待办任务"})
    resp = client.put("todos/0/done")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_done"] is True


def test_delete_todo():
    client.post("/todos", json={"content": "待删除任务"})
    resp = client.delete("/todos/0")
    assert resp.status_code == 200
    assert resp.json()["message"] == "id 0 删除成功"
    resp_after = client.get("/todos")
    assert len(resp_after.json()) == 0


# API异常场景
def test_operate_not_exist_id():
    # 修改不存在的id
    resp_put = client.put("/todos/999/done")
    assert resp_put.status_code == 404
    assert resp_put.json()["detail"] == "待办不存在"
    # 删除不存在的id
    resp_del = client.delete("/todos/999")
    assert resp_del.status_code == 404
    assert resp_del.json()["detail"] == "待办不存在"