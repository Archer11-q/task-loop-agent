"""30轮长对话不爆上下文

跑法：
CONTEXT_BUDGET_TOKENS=1200 KEEP_RECENT_BLOCKS=4 python -m scripts.demo_context
"""
from pydantic.v1.networks import host_regex

from app.agent.context import split_blocks, split_system
from app.agent.loop import run
from app.config import CONTEXT_BUDGET_TOKENS, KEEP_RECENT_BLOCKS

ROUNDS = 30

# 轮流问三类问题：各自会打中不同工具，让每轮都产生 tool 消息
QUESTIONS = [
    "现在几点了？",
    "我现在有几条待办？",
    "帮我算一下18*60-1080等于多少",
]


def main() -> None:
    history: list[dict] | None = None

    for i in range(1, ROUNDS + 1):
        question = QUESTIONS[(i - 1) % len(QUESTIONS)]
        print(f"\n========== 第 {i}/{ROUNDS} 轮：{question} ==========")
        answer, history = run(question, messages=history)
        print(f"答案：{answer}")

    _, rest = split_system(history)
    blocks = split_blocks(rest)
    print(
        f"\n【汇总】共 {ROUNDS} 轮对话；"
        f"当前历史 {len(history)} 条 / {len(blocks)} 轮"
        f"（保留上限 {KEEP_RECENT_BLOCKS} 轮，预算 {CONTEXT_BUDGET_TOKENS} tok）"
    )


if __name__ == "__main__":
    main()
