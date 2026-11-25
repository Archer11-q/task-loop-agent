import ast
import json
import operator
from datetime import datetime

"""内置工具：计时器 与 当前时间。"""

# ============ 计算器 ============
CALCULATE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": (
            "计算一个数学表达式，支持 + - * / // % ** 与括号。"
            "需要算数、计算时间差（如18*60-1050）时调用，不要自己心算"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "纯数字表达式，例如（18*60）-1050.不要带单位、中文或等号。",
                }
            },
            "required": ["expression"],
        },
    },
}

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def _eval_node(node):
    """只放行数字、四则运算和括号

    不用eval()：模型生成的字符串不可信输入，eval能执行任意代码
    """
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("指数过大")
        return _OPS[type(node.op)](left, right)

    # 一元运算：-10、+7
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval_node(node.operand)  # 取符号作用的对象
        return value if isinstance(node.op, ast.UAdd) else -value

    # 常量直接返回值
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    raise ValueError("只支持数字与 + - * / // % ** 和括号")


def calculate(expression: str) -> str:
    """计算表达式，返回JSON字符串"""
    expression = (expression or "").strip()
    if not expression:
        return json.dumps({"ok": False, "error": "表达式为空"}, ensure_ascii=False)
    if len(expression) > 100:
        return json.dumps({"ok": False, "error": "表达式过长"}, ensure_ascii=False)

    try:
        tree = ast.parse(expression, mode="eval")  # 只解析单个表达式
        value = _eval_node(tree.body)
    except (SystemError, ValueError, ZeroDivisionError, TypeError) as e:
        return json.dumps({"ok": False, "error": f"计算失败：{e}"}, ensure_ascii=False)

    # 5.0应该返回5
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return json.dumps(
        {"ok": True, "expression": expression, "result": value}, ensure_ascii=False)


# ============ 当前时间 ============
CURRENT_TIME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "current_time",
        "description": (
            "获取本机当前日期时间，并附带“距离今天0点的分钟数”，"
            "用于计算距离某个时刻还有多久。"
        ),
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
}

_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def current_time() -> str:
    """返回当前时间，附带 minute_since_midnight 供模型算时间差。"""
    now = datetime.now()
    return json.dumps(
        {
            "ok": True,
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": _WEEKDAYS[now.weekday()],
            "hour": now.hour,
            "minute": now.minute,
            # 18:00下班=1080分钟；模型拿这个值和1080相减即可
            "minutes_since_midnight": now.hour * 60 + now.minute,
        },
        ensure_ascii=False,
    )
