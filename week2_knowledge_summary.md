# 第二周 知识总结文档

> AI 转行应用开发 — Week 2：SQL、数据库、CRUD、Streamlit 界面  
> 对应学习计划文档第 2 周全部内容

---

## 目录

1. [SQL 基础](#1-sql-基础)
2. [SQLite 与数据库选型](#2-sqlite-与数据库选型)
3. [SQLAlchemy 2.0 核心概念](#3-sqlalchemy-20-核心概念)
4. [SQLModel：ORM + Pydantic 融合](#4-sqlmodelorm--pydantic-融合)
5. [FastAPI + 数据库集成模式](#5-fastapi--数据库集成模式)
6. [Streamlit 核心概念](#6-streamlit-核心概念)
7. [Streamlit session_state 深度解析](#7-streamlit-session_state-深度解析)
8. [Streamlit 表单与回调函数](#8-streamlit-表单与回调函数)
9. [Streamlit 调用 FastAPI（前后端分离）](#9-streamlit-调用-fastapi前后端分离)
10. [RAG 系统：为什么 documents 和 chunks 必须分开](#10-rag-系统为什么-documents-和-chunks-必须分开)
11. [项目结构最佳实践](#11-项目结构最佳实践)
12. [常见问题与调试技巧](#12-常见问题与调试技巧)

---

## 1. SQL 基础

### 1.1 什么是 SQL

SQL（Structured Query Language）是操作关系型数据库的标准语言。所有关系型数据库（SQLite、PostgreSQL、MySQL）都使用 SQL，差异只在少数语法细节。

### 1.2 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| 表（Table） | 数据的二维网格结构 | Excel 的一个 Sheet |
| 行（Row） | 表中的一条记录 | Excel 的一行 |
| 列（Column） | 表中的一个字段 | Excel 的一列 |
| 主键（Primary Key） | 唯一标识每行的列 | 身份证号 |
| 外键（Foreign Key） | 关联另一张表主键的列 | 指向另一张表的指针 |
| 索引（Index） | 加速查询的数据结构 | 书的目录 |

### 1.3 基本操作语法

```sql
-- 创建表
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 自增主键
    title TEXT NOT NULL,                      -- 不允许为空
    content TEXT,                             -- 允许为空
    file_type TEXT DEFAULT 'txt',            -- 默认值
    created_at TEXT DEFAULT (datetime('now'))
);

-- 插入数据（占位符 ? 防 SQL 注入）
INSERT INTO documents (title, content) VALUES (?, ?);

-- 查询所有
SELECT * FROM documents;

-- 条件查询
SELECT * FROM documents WHERE file_type = 'markdown';

-- 模糊查询
SELECT * FROM documents WHERE title LIKE '%FastAPI%';

-- 排序 + 分页
SELECT * FROM documents ORDER BY created_at DESC LIMIT 10 OFFSET 0;

-- 更新
UPDATE documents SET title = ? WHERE id = ?;

-- 删除
DELETE FROM documents WHERE id = ?;

-- 聚合统计
SELECT file_type, COUNT(*) as cnt FROM documents GROUP BY file_type;

-- JOIN 连接查询
SELECT d.title, c.chunk_text
FROM documents d
JOIN chunks c ON d.id = c.doc_id
WHERE d.id = 1;
```

### 1.4 外键与关系

```sql
-- 定义外键：chunks.doc_id → documents.id
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    doc_id INTEGER NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES documents(id)   -- 外键约束
);
```

外键的作用：
- **参照完整性**：chunks.doc_id 必须对应一个已存在的 documents.id
- **级联操作**：删除 document 时，可自动删除关联的 chunks
- **数据一致性**：防止"指向不存在文档的块"

> **注意**：SQLite 默认不强制外键约束，需要执行 `PRAGMA foreign_keys = ON;` 开启。

---

## 2. SQLite 与数据库选型

### 2.1 SQLite 特点

| 特性 | 说明 |
|------|------|
| 嵌入式 | 整个数据库是一个文件，无需安装服务器 |
| 零配置 | 不需要用户名、密码、端口 |
| 轻量 | 适合开发、测试、单机小应用 |
| 并发限制 | 同一时间只允许一个写操作 |
| 类型宽松 | 数据类型是建议性的（flexible typing） |

### 2.2 SQLite vs PostgreSQL

| 维度 | SQLite | PostgreSQL |
|------|--------|------------|
| 部署 | 嵌入式，一个文件 | 独立服务器，需安装运行 |
| 并发 | 读并发、写串行 | 高并发读写，MVCC 机制 |
| 类型 | 弱类型 | 严格类型检查 |
| 功能 | 基础 SQL | 复杂查询、JSONB、全文搜索 |
| 适用 | 学习、原型、移动端 | 生产环境、多用户应用 |
| 网络 | 本地文件 | TCP/IP 远程连接 |

### 2.3 学习建议

1. **先用 SQLite**：快速上手，专注于 SQL 本身而不是运维
2. **了解 PostgreSQL**：知道它解决了什么问题（并发、类型、功能）
3. **迁移成本低**：SQLAlchemy/SQLModel 自动生成 SQL，切换数据库只需改连接字符串

---

## 3. SQLAlchemy 2.0 核心概念

SQLAlchemy 是 Python 最强大的数据库工具库，分为两层：

- **Core 层**：Schema-centric，接近原生 SQL 但提供 Python 化的构建方式
- **ORM 层**：Object-centric，把表映射为 Python 类

> Week 2 重点是 ORM 层，配合 SQLModel 使用。

### 3.1 Engine（引擎）

Engine 是数据库连接的"工厂"，负责管理连接池和与数据库的通信。

```python
from sqlalchemy import create_engine

# SQLite 内存数据库（学习用）
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

# SQLite 文件数据库
engine = create_engine("sqlite:///mydb.sqlite3")

# PostgreSQL（生产用，需要 psycopg2 驱动）
engine = create_engine("postgresql+psycopg2://user:pass@host:5432/dbname")
```

- `echo=True`：打印所有生成的 SQL 语句（学习时非常有用）
- Engine 是**懒连接**：只在执行第一条 SQL 时才真正建立数据库连接

### 3.2 Session（会话）

Session 是 ORM 操作的核心入口，管理所有与数据库的交互。

```python
from sqlalchemy.orm import Session

# 创建 session
with Session(engine) as session:
    # 查询
    hero = session.get(Hero, 1)            # 按主键查
    heroes = session.scalars(stmt).all()   # 查多条并转为 ORM 对象

    # 新增
    hero = Hero(name="superman", secret_name="Clark")
    session.add(hero)
    session.commit()  # 提交事务

    # 更新（ORM 自动追踪）
    hero.name = "batman"
    session.commit()  # 自动检测变更并 UPDATE

    # 删除
    session.delete(hero)
    session.commit()
```

**关键方法对比**：

| 方法 | 行为 | 使用场景 |
|------|------|----------|
| `session.flush()` | 发送 SQL 但不提交 | 需要获取数据库生成的值（如自增 ID） |
| `session.commit()` | 提交事务 | 持久化所有变更 |
| `session.refresh(obj)` | 从数据库重新加载对象 | commit 后获取数据库当前值 |
| `session.rollback()` | 回滚未提交的变更 | 出错时撤销操作 |

### 3.3 DeclarativeBase（声明式基类）

现代 ORM 定义表的方式：

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass  # 所有 ORM 模型的共享基类

class User(Base):
    __tablename__ = "user_account"  # 映射到哪个数据库表

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    #          ↑ Python 类型提示         ↑ 数据库列定义
```

### 3.4 Core 查询 vs ORM 查询

```python
# Core 方式（接近原生 SQL，返回行对象）
from sqlalchemy import select
stmt = select(user_table).where(user_table.c.name == "spongebob")
result = conn.execute(stmt)
for row in result:
    print(row.name, row.fullname)

# ORM 方式（返回 Python 对象）
stmt = select(User).where(User.name == "spongebob")
users = session.scalars(stmt).all()   # scalars() 返回 ORM 对象迭代器
for user in users:
    print(user.name, user.fullname)
```

### 3.5 relationship（ORM 关系）

定义表之间的关联，让 ORM 自动处理 JOIN：

```python
class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    # 一对多：一个用户有多个地址
    addresses: Mapped[List["Address"]] = relationship(back_populates="user")

class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    # 多对一反向
    user: Mapped["User"] = relationship(back_populates="addresses")

# 使用：直接访问属性即可获取关联数据
spongebob = session.get(User, 1)
print(spongebob.addresses)  # 自动加载所有关联地址（懒加载）
```

**预加载策略**（避免 N+1 查询问题）：

```python
from sqlalchemy.orm import selectinload, joinedload

# selectinload：发 2 条 SQL（SELECT users + SELECT addresses WHERE user_id IN (...)）
stmt = select(User).options(selectinload(User.addresses))

# joinedload：发 1 条 SQL（LEFT OUTER JOIN）
stmt = select(User).options(joinedload(User.addresses))
```

> 经验法则：`selectinload` 适用于一对多，`joinedload` 适用于多对一。

---

## 4. SQLModel：ORM + Pydantic 融合

SQLModel 是 SQLAlchemy 2.0 + Pydantic v2 的结合体，专为 FastAPI 设计。一个类同时是：
- 数据库表定义（SQLAlchemy ORM）
- 数据校验模型（Pydantic）

### 4.1 模型分层模式

在 RAG 项目中我们使用这样的分层：

```python
# 第 1 层：Base — 公共字段
class DocumentBase(SQLModel):
    title: str
    content: str
    file_type: str = "txt"

# 第 2 层：Table — 数据库表模型（带 table=True）
class Document(DocumentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# 第 3 层：Public — 返回给前端的模型（隐藏敏感字段）
class DocumentPublic(DocumentBase):
    id: int
    created_at: datetime
    chunk_count: int = 0

# 第 4 层：Create — 创建时的请求体
class DocumentCreate(DocumentBase):
    pass

# 第 5 层：Update — 更新时的请求体（所有字段可选）
class DocumentUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    file_type: Optional[str] = None
```

### 4.2 为什么要分层

| 层 | 作用 | 关键区别 |
|----|------|----------|
| Table | 数据库存储 | 包含 secret、时间戳等所有字段 |
| Public | 对外返回 | **排除敏感字段（如 secret_name）** |
| Create | 输入校验 | 不含 id（数据库自动生成） |
| Update | 部分更新 | 所有字段 Optional |

### 4.3 field() 常用参数

```python
from sqlmodel import Field

class Example(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)           # 创建索引，加速查询
    age: int = Field(default=0, gt=0)       # 校验：大于 0
    email: str = Field(max_length=100)       # 校验：最大长度
    # gt: 大于, ge: 大于等于, lt: 小于, le: 小于等于
```

---

## 5. FastAPI + 数据库集成模式

### 5.1 依赖注入数据库会话

这是 FastAPI + SQLModel 的**标准模式**：

```python
from typing import Annotated
from fastapi import Depends

def get_session():
    """每个请求获取一个独立的数据库会话"""
    with Session(engine) as session:
        yield session  # yield 确保请求结束后自动关闭 session

# 定义类型别名，方便复用
SessionDep = Annotated[Session, Depends(get_session)]

# 在路由中使用（FastAPI 自动注入）
@app.post("/documents/")
def create_doc(doc: DocumentCreate, session: SessionDep):
    db_doc = Document.model_validate(doc)
    session.add(db_doc)
    session.commit()
    session.refresh(db_doc)
    return db_doc
```

**为什么用 yield 而不是 return？**
- `yield` 让 `get_session()` 成为生成器
- with 块在请求处理期间保持 session 打开
- 请求返回后自动执行 with 块的退出（关闭 session）
- 绝不遗漏关闭连接

### 5.2 生命周期事件

```python
@app.on_event("startup")
def on_startup():
    """应用启动时执行一次"""
    create_db_and_tables()  # 建表

@app.on_event("shutdown")
def on_shutdown():
    """应用关闭时执行一次"""
    # 清理资源（如关闭连接池）
```

### 5.3 response_model 的作用

```python
@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)  # 输入校验用 HeroCreate
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero  # 实际返回的是 Hero 对象（包含 secret_name）
    # FastAPI 根据 response_model=HeroPublic 自动：
    #   1. 过滤掉 secret_name 字段
    #   2. 验证返回数据格式
    #   3. 生成 API 文档
```

这是最重要的安全模式：**输入校验和输出过滤分离**。

---

## 6. Streamlit 核心概念

### 6.1 运行模型

Streamlit 不是传统的"事件驱动"框架。它的运行模型是 **"从上到下执行，每次交互都重新运行整个脚本"**。

```
用户点击按钮
    → Streamlit 检测到交互
    → 从头到尾重新执行整个 .py 文件
    → 重新渲染整个页面
```

**这对编程意味着什么？**

```python
# 错误理解（这在 Streamlit 中不行）
counter = 0

if st.button("加 1"):
    counter += 1  # 永远不会生效！因为每次重新运行 counter 都会重置为 0

st.write(counter)  # 永远显示 0
```

```python
# 正确用法（用 session_state 持久化状态）
if "counter" not in st.session_state:
    st.session_state.counter = 0  # 只在首次运行时初始化

if st.button("加 1"):
    st.session_state.counter += 1

st.write(st.session_state.counter)  # 正常累加
```

### 6.2 常用输入组件

| 组件 | 代码 | 用途 |
|------|------|------|
| 按钮 | `st.button("点击")` | 触发操作 |
| 文本输入 | `st.text_input("标签")` | 单行文本 |
| 文本域 | `st.text_area("标签")` | 多行文本 |
| 数字输入 | `st.number_input("标签", min_value=0)` | 数字 |
| 下拉选择 | `st.selectbox("标签", options=[...])` | 单选 |
| 单选框 | `st.radio("标签", options=[...])` | 单选（全部可见） |
| 文件上传 | `st.file_uploader("标签")` | 上传文件 |

### 6.3 常用展示组件

| 组件 | 代码 | 用途 |
|------|------|------|
| 标题 | `st.title("标题")` | H1 |
| 副标题 | `st.subheader("副标题")` | H3 |
| 文本 | `st.write("文本")` | 自动格式 |
| Markdown | `st.markdown("**粗体**")` | Markdown 渲染 |
| 数据框 | `st.dataframe(df)` | 可排序表格 |
| 度量卡片 | `st.metric("标签", 42)` | 数值展示 |
| 代码块 | `st.code("print(1)")` | 语法高亮 |
| 成功/警告 | `st.success()` / `st.warning()` / `st.error()` | 通知 |

### 6.4 布局组件

```python
# 侧边栏
with st.sidebar:
    st.title("导航")

# 多列布局
col1, col2 = st.columns(2)
with col1:
    st.write("左侧")
with col2:
    st.write("右侧")

# 展开折叠
with st.expander("点击展开"):
    st.write("隐藏的内容")

# 占位符（动态更新）
placeholder = st.empty()
placeholder.write("加载中...")
# ... 后续替换
placeholder.write("加载完成！")
```

---

## 7. Streamlit session_state 深度解析

### 7.1 为什么需要 session_state

Streamlit 的重新运行机制意味着：**所有普通 Python 变量在交互后都会丢失**。session_state 是唯一能在多次重新运行之间保持值的机制。

### 7.2 基本操作

```python
# 初始化（检查 key 是否存在）
if "count" not in st.session_state:
    st.session_state.count = 0

# 读取
current = st.session_state.count

# 写入
st.session_state.count = 100

# 删除
del st.session_state.count

# 使用 widget 的 key 自动绑定
st.number_input("输入值", key="increment_value")
# 现在 st.session_state.increment_value 自动保持用户输入
```

### 7.3 回调函数中使用 session_state

这是本周学到的重要模式：

```python
import datetime

# 初始化
if "count" not in st.session_state:
    st.session_state.count = 0
    st.session_state.last_updated = datetime.datetime.now().strftime("%H:%M:%S")

# 回调函数：在表单提交时执行
def update_counter():
    st.session_state.count += st.session_state.increment_value
    st.session_state.last_updated = datetime.datetime.now().strftime("%H:%M:%S")

with st.form(key="my_form"):
    st.number_input("Enter a value", value=0, step=1, key="increment_value")
    st.form_submit_button(label="Update", on_click=update_counter)
    #                    ↑ on_click 参数：提交时调用回调函数，不触发完整重新运行

st.write("Current Count =", st.session_state.count)
st.write("Last Updated =", st.session_state.last_updated)
```

### 7.4 session_state 常见模式

| 模式 | 示例 | 适用场景 |
|------|------|----------|
| 计数器 | `st.session_state.count += 1` | 分页、进度 |
| 标志位 | `st.session_state.submitted = True` | 表单提交状态 |
| 缓存数据 | `st.session_state.docs = api_result` | 避免重复请求 |
| 页面状态 | `st.session_state.current_page = "home"` | 多页面导航 |
| Widget 状态 | 通过 `key=` 参数自动绑定 | 所有 st.xxx 组件 |

### 7.5 Widget key 自动绑定机制

```python
# 给 widget 传 key 参数，它的值会自动存入 session_state
st.text_input("姓名", key="user_name")
# → st.session_state.user_name 始终等于输入框当前值

st.checkbox("同意协议", key="agreed")
# → st.session_state.agreed 始终等于 checkbox 当前值

# 在回调中读取很方便
def on_submit():
    name = st.session_state.user_name   # 直接读当前值
    agreed = st.session_state.agreed
```

---

## 8. Streamlit 表单与回调函数

### 8.1 st.form 的作用

```python
with st.form(key="my_form", clear_on_submit=True):
    name = st.text_input("姓名")
    age = st.number_input("年龄", min_value=0, max_value=150)
    submitted = st.form_submit_button("提交")

if submitted:
    st.write(f"你好 {name}，年龄 {age}")
```

**没有 st.form 时的问题**：
- 用户每输入一个字符，整个脚本重新运行
- 多次触发不必要的计算和 API 调用
- 用户体验差

**有 st.form 时**：
- 所有输入变化不会触发重新运行
- 只有点击"提交"按钮才触发
- 相当于把多个输入"打包"成一个事务

### 8.2 on_click 回调 vs if submitted

```python
# 方式 1：on_click 回调（适合简单操作）
def handle_submit():
    st.session_state.count += 1

st.form_submit_button("提交", on_click=handle_submit)

# 方式 2：判断返回值（适合需要访问表单变量的复杂场景）
submitted = st.form_submit_button("提交")
if submitted:
    result = api_post("/documents/", {"title": title, "content": content})
    if result:
        st.success("创建成功")
```

**选择建议**：
- 操作不依赖表单内的具体值 → on_click 回调
- 需要在提交后访问表单变量、调用 API、展示结果 → if submitted 模式

### 8.3 表单回调的执行顺序

```python
def on_submit():
    # 回调函数在"重新运行"之前执行
    # 此时 session_state 中的 widget 值已更新
    st.session_state.result = st.session_state.input_value * 2

with st.form("form"):
    st.number_input("输入", key="input_value")
    st.form_submit_button("计算", on_click=on_submit)

# 重新运行时显示结果
if "result" in st.session_state:
    st.write("结果:", st.session_state.result)
```

**执行流程**：
1. 用户点击"计算"
2. Streamlit 用 widget 的最新值更新 session_state
3. 执行 `on_submit()` 回调函数
4. 从上到下重新运行整个脚本

---

## 9. Streamlit 调用 FastAPI（前后端分离）

### 9.1 架构图

```
┌─────────────────┐     HTTP (requests)     ┌──────────────────┐
│   Streamlit      │ ───────────────────────→ │   FastAPI         │
│   (前端界面)      │ ←─────────────────────── │   (后端 API)       │
│   :8501          │     JSON 响应            │   :8000           │
└─────────────────┘                          └────────┬─────────┘
                                                      │
                                                      │ SQLAlchemy
                                                      │
                                             ┌────────▼─────────┐
                                             │   SQLModel ORM    │
                                             └────────┬─────────┘
                                                      │
                                                      │ SQL
                                                      │
                                             ┌────────▼─────────┐
                                             │   week2_rag.db   │
                                             │   (SQLite)        │
                                             └──────────────────┘
```

### 9.2 使用 requests 库调用

```python
import requests

API_BASE_URL = "http://127.0.0.1:8000"

# GET 请求
resp = requests.get(f"{API_BASE_URL}/documents/", params={"limit": 20}, timeout=10)
resp.raise_for_status()  # 如果不是 2xx，抛出异常
docs = resp.json()

# POST 请求
resp = requests.post(
    f"{API_BASE_URL}/documents/",
    json={"title": "我的笔记", "content": "...", "file_type": "txt"},
    timeout=10
)
if resp.status_code == 200:
    result = resp.json()

# DELETE 请求
resp = requests.delete(f"{API_BASE_URL}/documents/1", timeout=10)
```

### 9.3 统一封装（DRY 原则）

在 `week2_streamlit_app.py` 中，我们封装了三个工具函数：

```python
def api_get(endpoint: str, params=None) -> Optional[dict]:
    """所有 GET 请求的统一入口，包含错误处理"""
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.session_state.notification = ("❌ 无法连接后端", "error")
        return None
    except Exception as e:
        st.session_state.notification = (f"❌ 请求失败: {e}", "error")
        return None
```

这样做的好处：
- **不重复**：错误处理逻辑只写一次
- **统一用户体验**：所有错误都通过相同的通知机制展示
- **易调试**：只需在这一处修改错误处理逻辑

### 9.4 启动两个服务的命令

```powershell
# 终端 1：启动后端
fastapi dev week2_doc_api.py

# 终端 2：启动前端
streamlit run week2_streamlit_app.py
```

---

## 10. RAG 系统：为什么 documents 和 chunks 必须分开

### 10.1 核心问题

大语言模型（LLM）有**上下文窗口限制**，不能接收无限长的文本。

- GPT-4o: 128K tokens（约 10 万个中文字）
- DeepSeek-V3: 128K tokens
- 但有效注意力范围通常更短

### 10.2 为什么不直接把整篇文档发给模型

| 问题 | 后果 |
|------|------|
| Token 限制 | 长文档超出模型窗口，直接报错 |
| 成本 | 每轮对话都传整篇文档，API 费用指数增长 |
| 准确度 | 模型在长上下文中容易"迷失"，忽略关键信息 |
| 引用困难 | 无法精确定位答案来自哪个段落 |

### 10.3 分离的好处

```
┌─────────────────────────────────────────────┐
│              documents 表                    │
│  id │ title          │ content (全文)        │
│  1  │ "FastAPI 笔记"  │ "# FastAPI...        │
│                                  │           │
│                    文本切分       │           │
│                                  ▼           │
│              chunks 表                        │
│  id │ doc_id │ chunk_index │ chunk_text      │
│  1  │   1    │      0      │ "# FastAPI 是.." │
│  2  │   1    │      1      │ "一个现代的 Web.."│
│  3  │   1    │      2      │ "框架，它基于.." │
│  ...│  ...   │     ...     │      ...        │
└─────────────────────────────────────────────┘
```

**分离的好处**：

1. **精准检索**：只需检索最相关的几个 chunk（而非整篇文档）
2. **精准引用**：可以说"答案来自文档 A 的第 3 段"
3. **独立更新**：修改文档时只需重新切分该文档的 chunks
4. **元数据过滤**：可按 chunk 级别筛选（文档类型、时间、来源）
5. **混合检索**：不同文档的 chunks 可以混合排序

### 10.4 文本切分策略对比

| 策略 | 方式 | 优点 | 缺点 |
|------|------|------|------|
| 固定字符 | 每 N 个字符切一刀 | 简单快速 | 可能在词中间切断 |
| 固定字符 + 重叠 | 同上，相邻块有重叠 | 减少信息断裂 | 有冗余存储 |
| 按段落切 | 以 `\n\n` 为边界 | 语义更完整 | 段落长度不均 |
| 语义切分 | 用 embedding 判断语义边界 | 最优质量 | 需要调用 LLM |
| 递归字符切分 | 按 `\n\n` → `\n` → `。` → `，` 优先级逐步切 | 平衡效果 | 稍复杂 |

Week 2 我们使用的是**固定字符 + 重叠**，这是最基础的策略，也是学习中最好的起点。

---

## 11. 项目结构最佳实践

### 11.1 第二周项目的文件组织

```
FastAPI/
├── week2_config.py          # 所有配置集中管理
├── week2_models.py          # 数据库表模型定义
├── week2_doc_api.py         # FastAPI 后端（可独立运行）
├── week2_streamlit_app.py   # Streamlit 前端（可独立运行）
├── week2_rag.db             # SQLite 数据库文件（自动生成）
└── week2_knowledge_summary.md  # 本知识总结文档
```

### 11.2 模块职责划分

| 文件的职责 | 说明 |
|-----------|------|
| `week2_config.py` | 所有可调参数（DB 路径、API 地址、chunk 大小） |
| `week2_models.py` | 表结构定义 + engine + get_session |
| `week2_doc_api.py` | 路由、业务逻辑、文本切分工具函数 |
| `week2_streamlit_app.py` | UI 渲染、用户交互、API 调用封装 |

### 11.3 设计原则

1. **单一职责**：每个文件只做一件事
2. **配置外置**：不在业务代码里硬编码 URL、路径
3. **前端不碰数据库**：Streamlit 只通过 API 获取数据，不直接连接数据库
4. **模型分层**：Base → Table → Public → Create → Update，各司其职

---

## 12. 常见问题与调试技巧

### 12.1 Streamlit 常见坑

**Q：为什么按钮点击后没反应？**
```
A：检查是否在回调函数中修改了 session_state。
   如果是 if st.button("xxx"): 模式，按钮后的代码在重新运行时会执行。
```

**Q：为什么表单提交后输入框被清空了？**
```
A：使用了 clear_on_submit=True，这是预期行为。如果不想清空，设为 False。
```

**Q：为什么 session_state 的值变回默认值了？**
```
A：可能在每次重新运行时重新赋值了。确保初始化用了 if "key" not in st.session_state 保护。
```

### 12.2 FastAPI 常见坑

**Q：数据库表不存在？**
```
A：确认 on_event("startup") 中调用了 create_db_and_tables()，
   或者手动运行一次 python -c "from week2_models import create_db_and_tables; create_db_and_tables()"
```

**Q：为什么 DELETE 文档后 chunk 还在？**
```
A：SQLite 默认不启用外键级联删除。需要手动删除关联的 chunks，
   或者在 relationship() 中添加 cascade="all, delete-orphan"。
```

**Q：422 错误是什么？**
```
A：请求数据校验失败。去 /docs 页面查看接口期望的字段类型和格式，
   对比自己发送的 JSON 是否匹配。
```

### 12.3 数据库调试技巧

```python
# 1. 用 echo 查看生成的 SQL
engine = create_engine("sqlite:///mydb.sqlite3", echo=True)

# 2. 用 SQLite 命令行直接查看
# sqlite3 week2_rag.db
# sqlite> .tables          -- 查看所有表
# sqlite> .schema documents -- 查看表结构
# sqlite> SELECT * FROM documents;

# 3. 用 FastAPI 的 /docs 测试接口
# 访问 http://127.0.0.1:8000/docs，使用 Try it out 手动测试每个接口
```

### 12.4 学习路径建议

```
第 1 步：理解 session_state（已完成 ✓）
    → 弄懂为什么 Streamlit 需要它

第 2 步：跑通 models + API（当前项目）
    → python week2_doc_api.py，然后访问 /docs 测试接口

第 3 步：跑通 Streamlit 调用 API
    → 同时启动两个服务，在 Streamlit 中上传文档，检查数据库是否有数据

第 4 步：理解 RAG 表设计
    → 思考为什么 documents 和 chunks 要分开，在问答页面手动查询

第 5 步：准备进入 Week 3
    → LLM API 调用 + Prompt 设计
```

---

## 附录 A：本周脚本速查

| 脚本 | 启动命令 | 访问地址 |
|------|----------|----------|
| FastAPI 后端 | `fastapi dev week2_doc_api.py` | http://127.0.0.1:8000/docs |
| Streamlit 前端 | `streamlit run week2_streamlit_app.py` | http://localhost:8501 |
| SQLAlchemy 教程 | `python week2_sql.py` | 控制台输出 |

## 附录 B：API 接口速查表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/stats/` | 数据库统计 |
| POST | `/documents/` | 创建文档（自动切分） |
| GET | `/documents/` | 文档列表（分页） |
| GET | `/documents/{id}` | 文档详情 |
| GET | `/documents/{id}/chunks` | 文档的文本块 |
| PATCH | `/documents/{id}` | 更新文档 |
| DELETE | `/documents/{id}` | 删除文档及其 chunks |
| POST | `/conversations/` | 创建会话 |
| GET | `/conversations/` | 会话列表 |
| POST | `/conversations/{id}/messages/` | 添加消息 |
| GET | `/conversations/{id}/messages/` | 会话消息列表 |

---

> 编写时间：2026-05-16  
> 对应学习计划：AI 转行应用开发学习计划 — Week 2  
> 下一步：Week 3 — LLM API、Prompt、结构化输出与模型封装
