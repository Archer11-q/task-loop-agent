import argparse
from storage import load_todos,save_todos
from storage import TodoJsonCorruptError
from models import Todo


"""实现CLI工具：【添加】、【列出】、【完成】以及【删除】四条指令
    数据存文件内存
"""

def main():
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

    args = parser.parse_args()


    try:
        todos: list = load_todos()

        # 路由分发
        if args.cmd=="add":
            todos.append(Todo(args.content,False))
            save_todos(todos)
            print(f"已添加：{args.content}")

        elif args.cmd=="list":
            if not todos:
                print("暂无待办")
            else:
                for idx,t in enumerate(todos):
                    if args.done and not t.is_done:
                        continue
                    status="[已完成] " if t.is_done else "[未完成]"
                    print(f"[{idx}] {status} {t.content}")

        elif args.cmd=="finish":
            if 0 <= args.id < len(todos):
                todos[args.id].is_done = True
                save_todos(todos)
                print(f"[已完成] {todos[args.id].content}")
            else:
                print(f"未找到该待办: {args.id}")

        elif args.cmd=="del":
            if 0 <= args.id < len(todos):
                items=todos[args.id]
                todos.pop(args.id)
                save_todos(todos)
                print(f"[已删除] {items.content}")
            else:
                print(f"未找到该待办: {args.id}")
    except TodoJsonCorruptError:
        print("错误：待办文件损坏")

if __name__ == "__main__":
    main()