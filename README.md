# task-loop-agent

命令行 + HTTP 双入口的待办(Todo)工具,存储后端可在 JSON 与 SQLite 之间一键切换.
分层设计: 入口层(CLI / API) 不直接接触存储细节,统一通过 `storage` 接口读写,
由配置项决定底层后端: 两个后端抛出同一父类的异常,错误处理在后端之间保持一致.

## 分层架构
```
入口层                                           存储接口层              存储后端
main.py(CLI入口) ──> cli.py(业务逻辑) ──┐
                                       ├──> storage.get_storage() ──> storage_json   (data/todo.json)
api.py(HTTP入口) ──────────────────────┘        (按配置路由)           storage_sqlite  (data/todo.db)
```

- **统一接口**: 两个后端实现同一套 `load_todos` / `save_todos`,入口层零改动即可切换
- **统一异常**: `TodoStorageCorruptError` 为父类，JSON/SQLite 各有子类；入口层只捕获父类

## 快速开始

要求: Python 3.12+（开发与验证环境: Ubuntu WSL / Python 3.14.4）

```
# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 运行测试
pytest

# 3a. 命令行使用
python -m app.main add 买牛奶
python -m app.main list
python -m app.main list --done  # 只看已完成
python -m app.main finish 0
python -m app.main del 0

# 3b. HTTP接口使用
uvicorn app.api:app --reload
# 浏览器打开http://127.0.0.1:8000/docs 可交互调试
```

## API一览
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/todos` | 列出全部待办 |
| POST | `/todos` | 新增（body: `{"content": "..."}`） |
| PUT | `/todos/{id}/done` | 标记完成 |
| DELETE | `/todos/{id}` | 删除 |

## 切换存储后端
默认使用 JSON 文件存储,启动前设置环境变量可切换为 SQLite,业务代码无需任何改动

```
STORAGE_BACKEND=sqlite uvicorn app.api:app --reload
STORAGE_BACKEND=sqlite python -m app.main list
```

# 目录说明
```
app/
  main.py          CLI 入口（argparse 解析与分发）
  api.py           FastAPI 入口（四个 REST 接口）
  cli.py           CLI 命令处理逻辑
  models.py        Todo（CLI 内部数据结构）/ TodoCreate（API 请求体校验）
  config.py        读取 STORAGE_BACKEND 环境变量
  exceptions.py    异常层级：父类 + JSON/SQLite 两个子类
  storage/
    __init__.py        get_storage()：按配置返回后端实例
    storage_json.py    JSON 后端（data/todo.json）
    storage_sqlite.py  SQLite 后端（data/todo.db）
tests/             pytest 测试（存储层 / 接口层）
conftest.py        pytest 根配置（将仓库根目录加入 sys.path）
data/              运行时数据（不入库，已在 .gitignore 中）
```

## 说明
- 待办数据持久化在 `data/` 目录,文件不存在会自动重建;文件损坏会抛出统一的
    `TodoStorageCorruptError`，入口层转换为友好提示
- 当前后端接口为全量读写(load + save),单条增量接口(add/update/delete)
  属于规划中的演进项,演进时两个后端会同步更新以保持接口一致