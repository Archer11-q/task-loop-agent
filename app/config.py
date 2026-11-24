import os


# storage层开关，json存储 || SQLite存储
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND","json")



# LLM配置
LLM_API_KEY = (os.getenv("LLM_API_KEY")
               or os.getenv("DASHSCOPE_API_KEY"))

LLM_BASE_URL = (os.getenv("LLM_BASE_URL")
                or os.getenv("DASHSCOPE_BASE_URL"))


LLM_MODEL=os.getenv("LLM_MODEL") or "qwen3.7-flash"