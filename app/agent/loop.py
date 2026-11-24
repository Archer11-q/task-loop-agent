import json

from app.llm import chat
from app.tools import TOOL_SCHEMA, execute_tool

"""最小tool calling闭环
    流程固定两步：
    1.带tools请求 -> 模型返回 tool_calls
    2.本地执行工具 -> 结果作为 role=tool 回传 -> 模型给出自然语言答案
"""

SYSTEM_PROMPT = "你是一个待办助手。需要查询待办时必须调用工具，不要臆造数据"


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


def run(task:str)->tuple[str,list[dict]]:
    """跑完一次“工具调用 -> 结果回传 -> 最终回答”，返回（答案，完整messages）。"""
    messaegs:list[dict]=[
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":task},
    ]

    # 第一轮：模型决定要不要调用工具
    first=chat(messaegs,tools=TOOL_SCHEMA)
    messaegs.append(first)

    tool_calls=first.get("tool_calls") or []
    if not tool_calls:
        # 模型没用工具直接作答
        return first.get("content",""),messaegs

    # 执行工具并把结果回传：必须紧跟assistant
    for tc in tool_calls:
        args=json.loads(tc["function"]["arguments"] or "{}")
        result=execute_tool(tc["function"]["name"],args)
        messaegs.append(
            {"role":"tool","tool_call_id":tc["id"],"content":result}
        )

    # 第二轮：模型基于工具结果给出最终回答
    second=chat(messaegs,tools=TOOL_SCHEMA)
    messaegs.append(second)
    return second.get("content",""),messaegs

if __name__ == "__main__":
    answer,messages=run("我现在有几条待办？")
    print(f"答案：{answer}")
    print_messages(messages)