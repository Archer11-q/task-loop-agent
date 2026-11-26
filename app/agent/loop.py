"""最小tool calling闭环
    流程固定两步：
    1.带tools请求 -> 模型返回 tool_calls
    2.本地执行工具 -> 结果作为 role=tool 回传 -> 模型给出自然语言答案
"""

import json
from app.agent.context import print_budget_panel, should_trim, trim_messages
from app.config import AGENT_MAX_TURNS
from app.exceptions import AgentMaxTurnsError
from app.llm import chat
from app.tools import TOOL_SCHEMA, execute_tool

SYSTEM_PROMPT = (
    "你是一个待办助手。规则："
    "1)需要待办数据时必须调用工具，不要臆造；"
    "2）需要算数或者时间差别时调用 calculate，不要自己心算；"
    "3）多步任务一次只做一步，拿到结果再决定下一步；"
    "4）信息足够时直接给出最终答案"
)


def print_messages(messages: list[dict]) -> None:
    """逐条打印 messages，用来指认每一轮的角色"""
    print("\n========== messages ==========")
    for i, m in enumerate(messages):
        role = m["role"]
        if role == "assistant" and m.get("tool_calls"):
            names = [tc["function"]["name"] for tc in m["tool_calls"]]
            raws_args = [tc["function"]["arguments"] for tc in m["tool_calls"]]
            print(f"[{i}] role=assistant  content={m.get('content')!r}")
            print(f"    tool_calls={names}  arguments={raws_args}")
        elif role == "tool":
            print(f"[{i}] role=tool tool_call_id={m['tool_call_id']}")
            print(f"    content={m['content']}")
        else:
            print(f"[{i}] role={role}   content={m.get('content')!r}")
    print("==============================\n")


def _trim_if_needed(
        history: list[dict], prompt_tokens: int, trace: bool
) -> tuple[list[dict], int, bool]:
    """超过水位就裁到 system + 最近 N 个对话轮，返回（新历史，丢弃条数，是否触发）。"""
    if not should_trim(prompt_tokens):
        return history, 0, False

    trimmed, dropped = trim_messages(history)
    if trace and dropped:
        print(f"          ⇒ 裁剪：丢弃 {dropped} 条更早消息，保留 system + 最近几轮")
    return trimmed, dropped, True


def run(
        task: str,
        messages: list[dict] | None = None,
        max_turns: int | None = None,
        trace: bool = True
) -> tuple[str, list[dict]]:
    """React循环 + 上下文管理。

    循环：调工具 -> 本地执行 -> 结果回传 -> 直到模型不再调工具
    退出条件：这一轮 assistant 没有 tool_calls （= 模型改用自然语言作答，即finish）
    保护：最多 max_turns 轮，超了直接抛 AgentMaxTurnsError
    返回：裁剪后的历史
    """

    limit = max_turns or AGENT_MAX_TURNS
    # 传进来直接聊，没传开新会话
    if messages is None:
        history: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]
    else:
        history = list(messages)  # 不原地改调用方的列表
        history.append({"role": "user", "content": task})

    total_prompt = 0
    total_completion = 0

    for turn in range(1, limit + 1):
        reply = chat(history, tools=TOOL_SCHEMA)
        history.append(reply.message)

        prompt_tokens = reply.usage.get("prompt_tokens") or 0
        total_prompt += prompt_tokens
        total_completion += reply.usage.get("completion_tokens") or 0

        tool_calls = reply.message.get("tool_calls") or []

        # 收尾轮：先把历史裁到安全线以内再返回，避免下次接龙带着超标历史请求
        if not tool_calls:
            history, dropped, fired = _trim_if_needed(history, prompt_tokens, trace)
            if trace:
                print_budget_panel(
                    turn, reply.usage, history, dropped, fired,
                    total_prompt, total_completion,
                )
            return reply.message.get("content", ""), history

        # 执行多个工具
        for tc in tool_calls:
            name = tc["function"]["name"]
            raw = tc["function"]["arguments"]
            try:
                args = json.loads(raw or "{}")
            except json.JSONDecodeError:
                result = f"错误：工具参数不是合法 JSON，收到的是：{raw!r}"
            else:
                result = execute_tool(name, args)

            history.append(
                {"role": "tool", "tool_call_id": tc["id"], "content": result}
            )

        history, dropped, fired = _trim_if_needed(history, prompt_tokens, trace)
        if trace:
            print_budget_panel(
                turn, reply.usage, history, dropped, fired,
                total_prompt, total_completion,
            )

    raise AgentMaxTurnsError(
        f"达到最大轮数 {limit} 仍未收尾，最后一条消息 role={history[-1]['role']}"
    )


if __name__ == "__main__":
    answer, messages = run("把明天开会加进待办，然后告诉我现在离下班还有多久")
    print(f"答案：{answer}")
    print_messages(messages)
