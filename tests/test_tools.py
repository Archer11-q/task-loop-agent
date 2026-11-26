"""工具层：5个工具的行为 + 分发兜底。用内存storage，不落盘。"""

import json
from app.tools import execute_tool
from app.tools.builtin_tools import calculate, current_time
from app.tools.todo_tools import add_todo, delete_todo, list_todos


# ---------- 待办三件套 ----------
def test_list_todos_empty(todo_store):
    assert json.loads(list_todos())["count"] == 0


def test_add_todo_then_list(todo_store):
    added = json.loads(add_todo("写周报"))

    assert added["ok"] is True
    assert added["count"] == 1
    assert json.loads(list_todos())["todos"][0]["content"] == "写周报"


def delete_todo_out_of_range(todo_store):
    result = json.loads(delete_todo(5))

    assert result["ok"] is False
    assert "不存在" in result["error"]


def test_storage_error_becomes_message(broken_todo_store):
    """存储坏了也不抛：返回错误 JSON，让模型直到发生了什么"""
    payload = json.loads(list_todos())

    assert "error" in payload


# ---------- 分发 ----------
def test_execute_tool():
    assert "未知工具" in execute_tool("nope", {})


def test_execute_argument_mismatch(todo_store):
    assert "参数不匹配" in execute_tool("add_todo", {"wrong": 1})


# ---------- 计算器 ----------
def test_calculate_time():
    assert json.loads(calculate("(18*60)-1080"))["result"] == 0


def test_calculater_zero_division():
    assert json.loads(calculate("1/0"))["ok"] is False


# ---------- 当前时间 ----------
def test_current_time():
    data = json.loads(current_time())

    assert data["ok"] is True
    assert 0 <= data["minutes_since_midnight"] < 24 * 60
