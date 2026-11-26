from .client import chat, get_client, LLMReply

"""LLM 调度层入口：外部只从这里拿 chat / get_client """

__all__ = ["chat", "get_client", "LLMReply"]
