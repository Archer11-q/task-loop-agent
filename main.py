import json
import argparse

"""实现CLI工具：【添加】、【列出】、【完成】以及【删除】四条指令
    数据存文件内存
"""


# 文件名称常量
TODO_FILE="todo.json"

# 加载函数：将文件内容加载到json
def load_todo():
    try:
        with open(TODO_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# 保存函数：执行增删改操作时修改文件
def save_todo(data):
    with open(TODO_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)   # 防止中文乱码，进行格式化

# 加载代办列表
todo_list:list=load_todo()


# 初始化命令行解析器，注册子命令add,list,finish,del
parser=argparse.ArgumentParser()
subs=parser.add_subparsers(dest="cmd")

# 添加功能，增加必填位置参数
add_p=subs.add_parser("add")
add_p.add_argument("content")

# 列出功能，增加可选参数--done
list_p=subs.add_parser("list")
list_p.add_argument("--done",action="store_true")

# 完成功能：位置参数，int，必填
finish_p=subs.add_parser("finish")
finish_p.add_argument("id",type=int)

# 删除功能，位置参数，int，必填
del_p=subs.add_parser("del")
del_p.add_argument("id",type=int)

args=parser.parse_args()


# 路由分发
if args.cmd=="add":
    todo_list.append([args.content,False])
    print(f"已添加：{args.content}")
    save_todo(todo_list)

elif args.cmd=="list":
    if len(todo_list) == 0:
        print("暂无待办")
    else:
        for idx,(content,is_done) in enumerate(todo_list):
            if args.done and not is_done:
                continue
            status="[已完成]" if is_done else "[未完成]"
            print(f"[{idx}] {status} {content}")

elif args.cmd=="finish":
    idx=args.id
    if idx<0 or idx>=len(todo_list):
        print(f"未找到该待办: {idx}")
    else:
        todo_list[idx][1] = True
        content = todo_list[idx][0]
        print(f"[已完成]{content}")
        save_todo(todo_list)

elif args.cmd=="del":
    idx = args.id
    if idx < 0 or idx >= len(todo_list):
        print(f"未找到该代办: {idx}")
    else:
        content = todo_list[idx][0]
        todo_list.pop(idx)
        print(f"[已删除]{content}")
        save_todo(todo_list)