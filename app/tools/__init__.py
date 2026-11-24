from .todo_tools import LIST_TODOS_SCHEMA,list_todos

"""工具层入口：注册表 + 分发"""


# 后续新增add_todo / finish_todo / calculator / now都放这
TOOL_SCHEMA=[LIST_TODOS_SCHEMA]



def execute_tool(name:str,args:dict)->str:
    """按名字分发到具体实现，永远返回字符串.

        未知工具/参数错误不抛异常：把错误文本交回模型，
        让模型决定是否重试/更换方案
    """
    if name == "list_todos":
        return list_todos()

    available=[s["function"]["name"] for s in TOOL_SCHEMA]  # 获取所有可用工具名称
    return f"错误：未知工具{name}，当前可用工具：{available}"
