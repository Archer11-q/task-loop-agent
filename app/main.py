import argparse
from app.cli import run

"""程序总入口: 仅负责参数解析,不包含任何业务逻辑"""

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
    run(args)

if __name__ == "__main__":
    main()