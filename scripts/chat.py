"""交互式会话：多轮对话落 SQLite，退出后可按会话恢复

跑法：
    python -m scripts.chat          # 只输出答案
    python -m scripts.chat --trace  # 同时打印每轮上下文预算面板
"""

import sys

from app.agent.loop import run
from app.storage.storage_session import SessionStore


def clean_text(s: str) -> str:
    """把非法 UTF-8 字节解出来的孤立代理项替换成 U+FFFD。

    终端送来的字节不是合法 UTF-8 时，Python 的 stdin 用 surrogateescape
    把它们兜成 \\udcXX 存进 str：屏幕上看着正常，但发请求时
    json.dumps().encode() 会抛 "surrogates not allowed"。
    在入口洗一次，里面的代码就不用再防。
    """
    return s.encode("utf-8", errors="replace").decode("utf-8")


def pick_session(store: SessionStore) -> tuple[str, list[dict], str]:
    """列会话 -> 选一个恢复/重建。返回（会话id，历史messages，标题）"""
    sessions = store.list_sessions()
    if sessions:
        print("已有会话：")
        for i, s in enumerate(sessions, 1):
            print(
                f"  {i}. [{s['id'][:8]}] {s['title']}"
                f"  ({s['message_count']} 条, {s['updated_at']})"
            )
        choice = clean_text(input("输入编号恢复，回车新建，q 退出：").strip())
        if choice == "q":
            raise SystemExit(0)
        if choice.isascii() and choice.isdigit() and 1 <= int(choice) <= len(sessions):
            picked = sessions[int(choice) - 1]
            messages = store.load_messages(picked["id"])
            print(f"已恢复 [{picked['id'][:8]}]，历史 {len(messages)} 条\n")
            return picked["id"], messages, picked["title"]
    else:
        print("还没有会话，先新建一个。")

    title = clean_text(input("会话标题（回车用默认）：").strip()) or "未命名会话"
    session_id = store.create_session(title)
    print(f"已新建 [{session_id[:8]}]\n")
    return session_id, [], title


def main() -> None:
    trace = "--trace" in sys.argv
    store = SessionStore()
    session_id, messages, title = pick_session(store)

    print(f"会话：{title}    输入 /exit 退出")
    try:
        while True:
            text = clean_text(input("\n你：").strip())
            if not text:
                continue
            if text in ("/exit", "exit", "quit"):
                break

            # 新会话传 None ，恢复的会话把历史原样递回去
            answer, messages = run(text, messages=messages or None, trace=trace)
            print(f"助手: {answer}")
            store.replace_messages(session_id, messages)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C / Ctrl+D：已完成的轮次都已落库
        print("\n已中断。")
    finally:
        if messages:
            store.replace_messages(session_id, messages)
        store.close()
        print(f"会话已保存：[{session_id[:8]}]  用 python -m scripts.chat 可恢复")


if __name__ == "__main__":
    main()
