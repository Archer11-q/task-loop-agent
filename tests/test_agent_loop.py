"""循环层：只测控制流，LLM 被 mock 掉，不发真实请求、不花钱、结果确定"""
import json

import pytest

from app.agent.loop import run
from app.exceptions import AgentMaxTurnsError
from app.llm.client import LLMReply


def reply(content="", tool_calls=None, prompt=100):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return LLMReply(
        message=message,
        usage={"prompt_tokens": prompt, "completion_tokens": 5}
    )


def tool_call(call_id, name, arguments="{}"):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": arguments}
    }


@pytest.fixture
def fake_chat(monkeypatch):
    """按脚本依次返回reply：记录每次实际发出去的 message 快照"""

    def install(replies):
        sent = []

        def _chat(messages, tools=None):
            sent.append(list(messages))
            return replies.pop(0)

        monkeypatch.setattr("app.agent.loop.chat", _chat)
        return sent

    return install


def test_run_returns_direct_answer(fake_chat):
    sent = fake_chat([reply("你好")])

    answer, messages = run("在吗", trace=False)

    assert answer == "你好"
    assert [m["role"] for m in messages] == ["system", "user", "assistant"]


def test_run_executes_tool_then_answers(todo_store, fake_chat):
    sent = fake_chat([
        reply(tool_calls=[tool_call("c1", "add_todo", '{"content":"写周报"}')]),
        reply("已添加")
    ])

    answer, messages = run("加一条写周报", trace=False)

    assert answer == "已添加"
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool", "assistant"]

    tool_msg = messages[3]
    assert tool_msg["tool_call_id"] == "c1"
    assert json.loads(tool_msg["content"])["ok"] is True
    assert len(sent) == 2


def test_run_supports_multiple_tool_round(todo_store, fake_chat):
    fake_chat([
        reply(tool_calls=[tool_call("c1", "add_todo", '{"content":"A"}')]),
        reply(tool_calls=[tool_call("c2", "list_todos", "{}")]),
        reply("共 1 条"),
    ])

    answer, messages = run("加一条再查", trace=False)

    assert answer == "共 1 条"
    assert sum(1 for m in messages if m["role"] == "tool") == 2


def test_max_turns_raises(todo_store, fake_chat):
    """模型一直要调工具时，轮数保护必须抛异常而不是死循环"""
    fake_chat([reply(tool_calls=[tool_call("c1", "list_todos", "{}")])] * 3)

    with pytest.raises(AgentMaxTurnsError):
        run("查一下", max_turns=1, trace=False)


def test_bad_json_arguments_fed_back(todo_store, fake_chat):
    """模型给的参数不是合法json时，错误要回到模型而不是炸掉循环"""
    fake_chat([
        reply(tool_calls=[tool_call("c1", "list_todo", "not json")]),
        reply("收到错误")
    ])


def test_resume_appends_to_history(fake_chat):
    history = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"}
    ]
    sent = fake_chat([reply("a2")])

    answer, messages = run("u2", messages=history, trace=False)

    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user", "assistant"]
    assert sent[0][-1]["content"] == "u2"
    assert len(history) == 3  # 调用方传进来的列表没被就地修改
