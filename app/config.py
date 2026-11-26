import os
from pathlib import Path

from dotenv import load_dotenv

# 本地开发：加载仓库根 .env；override=False，真实环境变量优先
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# storage层开关，json存储 || SQLite存储
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "json")

# LLM配置
LLM_API_KEY = (os.getenv("LLM_API_KEY")
               or os.getenv("DASHSCOPE_API_KEY"))

LLM_BASE_URL = (os.getenv("LLM_BASE_URL")
                or os.getenv("DASHSCOPE_BASE_URL"))

LLM_MODEL = os.getenv("LLM_MODEL") or "qwen3.7-flash"

# agent循环：最大轮数，防止模型无限调工具
AGENT_MAX_TURNS = int(os.getenv("AGENT_MAX_TURNS", "8"))

# 上下文管理
CONTEXT_BUDGET_TOKENS = int(os.getenv("CONTEXT_BUDGET_TOKENS", "6000"))
KEEP_RECENT_BLOCKS = int(os.getenv("KEEP_RECENT_BLOCKS", "6"))
