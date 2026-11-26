from dataclasses import dataclass, field
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

"""LLM 调用层：全项目唯一创建 OpenAI 客户端的地方.
分层原因：
1.上层（agent/tools）不直接依赖openai SDK，换provider只改这一个文件；
2.只返回纯dict，message才能json.dump
3.加超时/重试/降级只动这个文件
"""

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not LLM_API_KEY:
            raise RuntimeError(
                "未找到 API key：请设置环境变量 LLM_API_KEY 或 DASHSCOPE_API_KEY"
            )
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client


def _to_message_dict(message: ChatCompletionMessage) -> dict:
    """只挑协议需要的字段回转

       转换原因：
       SDK对象不能直接放进messages传给接口，接口只认字典
       同时方便json.dumps序列化
    """
    data: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        data["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return data


@dataclass
class LLMReply:
    """一次调用的结果：assistant 消息 + token用量

    usage 存 API 返回的原值(prompt_tokens/completion_tokens/total_tokens)
    """
    message: dict
    usage: dict = field(default_factory=dict)


def chat(messages: list[dict], tools: list[dict] | None = None) -> LLMReply:
    """发一次chat.completions请求，返回assistant message的纯dict
       暂不做重试/超时/降级
    """

    kwargs = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0,  # 低温拿到稳定回复
    }
    if tools:  # 不能把None塞给SDK
        kwargs["tools"] = tools
    resp = get_client().chat.completions.create(**kwargs)
    # resp.usage在非流式下一定有；模型/网关异常可能为None
    usage = resp.usage.model_dump() if resp.usage else {}
    return LLMReply(message=_to_message_dict(resp.choices[0].message), usage=usage)
