"""上下文管理：分组与裁剪。全是纯函数，不花钱，不碰网络。"""
from calendar import month

import pytest

from app.agent import context


def msg(role, content="", **extra):
    return {"role": role, "content": content, **extra}


def test_split_blocks_groups_by_user():
    messages = [
        msg("user", "u1"),
        msg("assistant", "a1"),
        msg("user", "u2"),
        msg("tool", "r", tool_call_id="1"),
    ]
    assert [len(b) for b in context.split_blocks(messages)] == [2, 2]


def test_split_blocks_skips_system():
    assert context.split_blocks([msg("system", "s")]) == []


def test_trim_keeps_system_ans_recent_blocks(monkeypatch):
    monkeypatch.setattr(context, "KEEP_RECENT_BLOCKS", 1)
    messages = [
        msg("system", "s"),
        msg("user", "u1"),
        msg("assistant", "a1"),
        msg("user", "u2"),
        msg("assistant", "a2"),
    ]
    trimmed, dropped = context.trim_messages(messages)

    assert trimmed[0]['role'] == "system"
    assert [m["content"] for m in trimmed[1:]] == ["u2", "a2"]  # u1,a1因为上下位被截掉
    assert dropped == 2


def test_trim_never_splits_system(monkeypatch):
    monkeypatch.setattr(context, "KEEP_RECENT_BLOCKS", 1)
    call = {"id": "c1", "type": "function", "function": {"name": "current_time", "arguments": "{}"}}

    messages = [
        msg("system", "s"),
        msg("user", "u1"),
        msg("assistant", "a1"),
        msg("user", "u2"),
        msg("assistant", "", tool_calls=[call]),
        msg("tool", "r", tool_call_id="c1"),
        msg("assistant", "a2"),
    ]
    trimmed, _ = context.trim_messages(messages)

    assert [m["role"] for m in trimmed] == [
        "system", "user", "assistant", "tool", "assistant"
    ]
    # tool的tool_call_id仍能对上对面的assitant的tool_calls
    assert trimmed[3]["tool_call_id"] == trimmed[2]["tool_calls"][0]["id"]


def test_should_trim_uses_watermark(monkeypatch):
    monkeypatch.setattr(context, "CONTEXT_BUDGET_TOKENS", 1000)
    assert context.should_trim(749) is False
    assert context.should_trim(750) is True
