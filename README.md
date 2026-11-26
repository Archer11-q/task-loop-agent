# task-loop-agent

命令行 + HTTP 双入口的待办(Todo)服务，外加一个不依赖任何框架的手写mini-agent。

存储后端可在 JSON 与 SQLite 之间一键切换；agent 侧手写 ReAct 循环、工具注册表、
上下文裁剪与会话持久化。分层原则：入口层不接触存储细节，统一通过 `storage` 接口读写。

## 功能

- 待办服务：CLI 与 REST 双入口，同一套存储抽象
- 手写 agent 循环：模型决定调工具 -> 本地执行 -> 结果回传 -> 直到模型给出最终答案
- 5个工具：待办增/删/查，计算器、当前时间
- 上下文管理：按对话轮裁剪，历史超预算自动丢弃最旧的轮次
- 会话持久化：每轮落库，退出后可按会话恢复继续聊
- 测试：存储 / 接口 / 上下文 / 工具 / 循环五层，LLM 与存储全部替身化

## 快速开始

要求: Python 3.12+（开发与验证环境: Ubuntu WSL / Python 3.14.4）

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 填入模型密钥
pytest
```

```bash
python -m app.main add 买牛奶     # 命令行入口
python -m app.main list
uvicorn app.api:app --reload      # HTTP 入口，浏览器打开 /docs 调试
```

### 与 agent 对话

```bash
python -m scripts.chat            # 交互式，退出后可按会话恢复
python -m scripts.chat --trace    # 同时打印上下文预算面板
```

对话支持自然语言管理待办，例如「把明天开会加进待办」「我现在有几条待办」「现在离下班还有多久」。
每次问答结束自动落库，`/exit` 或 `Ctrl+C` 退出后重新启动，输入会话编号即可恢复历史继续聊。

### 测试

```bash
pytest                               # 全量
pytest tests/test_agent_loop.py -v   # 只看循环
```

测试覆盖存储、接口、上下文、工具、循环五层。循环层把模型调用替换为脚本化替身，
不发真实请求，因此测试快速、免费、结果确定。

## 架构

```
scripts/chat.py ──► storage_session.py ──► data/agent.db        （会话 / 消息）
      │
      └──► agent/loop.py                                        （ReAct 循环）
                │
                ├── llm/client.py ──────────► DeepSeek / 百炼 API
                ├── agent/context.py                            （上下文裁剪 / 预算）
                └── tools/__init__.py                           （注册表 + 分发）
                       │
                       ├── todo_tools.py ──► storage/ ──► data/todo.json | todo.db
                       └── builtin_tools.py                     （计算器 / 当前时间）
```

分层约束：`loop` 不认识数据库，`tools` 不认识模型，`llm` 不认识对话历史。

## 一次调用中的消息流转

一个提问通常产生两次模型调用——模型本身不能执行工具。

1. 带上 `system + user + 工具定义` 调用模型；模型返回 `assistant` 消息，`content` 为空，
   `tool_calls` 里写明要调哪个工具、参数是什么。
2. 本地执行工具，把结果作为 `role=tool` 的消息追加到历史，`tool_call_id` 与上一步的 `id` 对应。
3. 带着这段历史再次调用模型，模型基于工具结果给出自然语言答案。

循环的退出条件是「这一轮没有 `tool_calls`」，而不是「`content` 非空」——
发起工具调用时 `content` 本来就是空的。因此调用次数 = 1 + 工具调用次数。

## API一览

| 方法     | 路径                 | 说明                             |
|--------|--------------------|--------------------------------|
| GET    | `/todos`           | 列出全部待办                         |
| POST   | `/todos`           | 新增（body: `{"content": "..."}`） |
| PUT    | `/todos/{id}/done` | 标记完成                           |
| DELETE | `/todos/{id}`      | 删除                             |

> 分层细节、上下文策略与异常约定见 [docs/design.md](docs/design.md)。