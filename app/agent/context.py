"""上下文管理：按轮分组、超预算裁剪、打印预算面板。"""

from app.config import CONTEXT_BUDGET_TOKENS, KEEP_RECENT_BLOCKS

# 水位线：上一轮真实 prompt_tokens 超过预算的这个比例，就在本轮结束时裁剪
TRIM_WATERMARK = 0.75


def split_system(messages: list[dict]) -> tuple[dict | None, list[dict]]:
    """把 system 单独摘出来 —— 永远不参与裁剪，放在队首"""
    if messages and messages[0]['role'] == "system":
        return messages[0], messages[1:]
    return None, messages


def split_blocks(messages: list[dict]) -> list[list[dict]]:
    """按一轮切块：一条 user 到下一条 user 之间的所有消息算一轮"""

    blocks: list[list[dict]] = []  # system外的所有消息历史
    current: list[dict] = []  # 上一轮次的消息

    for message in messages:
        if message["role"] == "system":
            continue
        if message["role"] == "user" and current:
            blocks.append(current)
            current = [message]
        else:
            current.append(message)

    if current:
        blocks.append(current)
    return blocks


def should_trim(prompt_tokens: int) -> bool:
    """用上一轮真实 prompt_tokens 判断要不要裁剪。"""
    return prompt_tokens >= CONTEXT_BUDGET_TOKENS * TRIM_WATERMARK


def trim_messages(messages: list[dict]) -> tuple[list[dict], int]:
    """保留 system + 最近 KEEP_RECENT_BLOCKS 轮，返回 （新列表，丢弃条数）"""

    system, rest = split_system(messages)  # 分离system + 剩余消息
    blocks = split_blocks(rest)  # 获取所有非system消息历史

    if len(blocks) <= KEEP_RECENT_BLOCKS:
        return list(messages), 0  # 返回副本，避免修改原账本

    kept = [m for block in blocks[-KEEP_RECENT_BLOCKS:] for m in block]
    trimmed = ([system] if system else []) + kept
    return trimmed, len(messages) - len(trimmed)


def _bar(radio: float, width: int = 10) -> str:
    """ 打印 token 水位，使用率进度条"""
    radio = min(max(radio, 0.0), 1.0)
    filled = int(radio * width)
    return "▓" * filled + "░" * (width - filled)


def print_budget_panel(
        turn: int, usage: dict,
        messages: list[dict], dropped: int = 0, fired: bool = False,
        total_prompt: int = 0, total_completion: int = 0,
) -> None:
    """打印本轮上下文预算面板。

    turn    = 本次 run() 里第几次请求（while 循环的第几圈）
    dropped = 本次裁剪丢掉的条数
    fired   = 是否越过水位线（越线但无可裁，和"未触发"是两回事）
    """
    prompt_tokens = usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or 0
    ratio = prompt_tokens / CONTEXT_BUDGET_TOKENS

    _, rest = split_system(messages)
    blocks = split_blocks(rest)

    if not fired:
        trim_text = "未触发"
    elif dropped:
        trim_text = f"已裁剪：丢弃 {dropped} 条"
    else:
        trim_text = "已超水位，但块数≤保留上限，无可裁"

    print(
        f"┌─ 上下文预算 · 第{turn}次请求 ──────────────────\n"
        f"│ 预算 {CONTEXT_BUDGET_TOKENS:,} tok   "
        f"本轮 prompt {prompt_tokens:,} tok ({ratio:.0%}) {_bar(ratio)}\n"
        f"│ 本轮完成 {completion_tokens:,} tok   "
        f"累计 prompt {total_prompt:,} / 完成 {total_completion:,}\n"
        f"│ 历史 {len(messages)} 条 / {len(blocks)} 个对话轮"
        f"（保留上限 {KEEP_RECENT_BLOCKS} 个）\n"
        f"│ 裁剪 {trim_text}\n"
        f"└────────────────────────────────────────────────"
    )
