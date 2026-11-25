"""最小tool calling闭环
    流程固定两步：
    1.带tools请求 -> 模型返回 tool_calls
    2.本地执行工具 -> 结果作为 role=tool 回传 -> 模型给出自然语言答案
"""

import json
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


def run(
        task: str, max_turns: int | None = None, trace: bool = True
) -> tuple[str, list[dict]]:
    """React循环：调工具 -> 本地执行 -> 结果回传 -> 直到模型不再调工具。

    退出条件：这一轮 assistant 没有 tool_calls （= 模型改用自然语言作答，即finish）
    保护：最多 max_turns 轮，超了直接抛 AgentMaxTurnsError
    """
    limit=max_turns or AGENT_MAX_TURNS
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for turn in range(1,limit+1):
        message=chat(messages,tools=TOOL_SCHEMA)
        messages.append(message)

        tool_calls=message.get("tool_calls") or []
        if not tool_calls:
            if trace:
                print(f"第{turn}轮无工具调用 -> 循环结束")
            return message.get("content",""),messages

        if trace:
            print(f"[第{turn}轮] 调用工具：{[tc['function']['name'] for tc in tool_calls]}")

        # 调用多个工具
        for tc in tool_calls:
            name=tc["function"]["name"]
            raw=tc["function"]["arguments"]
            try:
                args=json.loads(raw or {})
            except json.JSONDecodeError:
                result=f"错误：工具参数不是合法 JSON，收到的是：{raw!r}"
            else:
                result=execute_tool(name,args)

            messages.append(
                {"role":"tool","tool_call_id":tc["id"],"content":result}
            )
            if trace:
                brief=result if len(result) <=100 else result[:100] +"…"
                print(f"          {name} → {brief}")

    raise AgentMaxTurnsError(
        f"达到最大轮数 {limit} 仍未收尾，最后一条消息 role={messages[-1]['role']}"
    )


if __name__ == "__main__":
    answer, messages = run("把明天开会加进待办，然后告诉我现在离下班还有多久")
    print(f"答案：{answer}")
    print_messages(messages)
