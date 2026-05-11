"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           SQLAlchemy 2.0 完整学习教程 —— VSCode 可直接运行版               ║
║   对应官方文档: https://docs.sqlalchemy.org/en/20/tutorial/                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

【环境准备】
    pip install sqlalchemy

【运行方式】
    - 整体运行: python sqlalchemy_2_tutorial.py
    - 逐节运行: 取消对应章节末尾的 section_X() 注释，单独运行

【目录】
    第 1 章  建立连接 —— Engine
    第 2 章  事务与 DBAPI
    第 3 章  数据库元数据（Table / MetaData）
    第 4 章  使用 ORM 映射类
    第 5 章  Core 方式增删改查
    第 6 章  ORM 方式增删改查（Session）
    第 7 章  使用 select() 查询
    第 8 章  关系（relationship）与 JOIN
    第 9 章  更新与删除
    第 10 章 综合示例：博客系统
"""

# ─────────────────────────────────────────────────────────────────────────────
# 统一导入（放最顶部，方便复用）
# ─────────────────────────────────────────────────────────────────────────────
from sqlalchemy import (
    create_engine, text, MetaData, Table, Column,
    Integer, String, ForeignKey,
    insert, select, update, delete,
    func, and_, or_, desc
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, Session
)
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# 第 1 章  建立连接 —— Engine
# ═══════════════════════════════════════════════════════════════════════════════
def section_1():
    print("\n" + "="*60)
    print("第 1 章：建立连接 —— Engine")
    print("="*60)

    # ── 1-1  SQLite 内存数据库（最适合学习，无需安装额外数据库）──
    engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
    #
    # echo=True  → 将所有 SQL 语句打印到控制台，学习时推荐开启
    #
    # 常见连接字符串格式：
    #   SQLite 文件:  "sqlite:///./mydb.sqlite3"
    #   PostgreSQL:   "postgresql+psycopg2://user:pass@host:5432/dbname"
    #   MySQL:        "mysql+pymysql://user:pass@host:3306/dbname"
    #   SQL Server:   "mssql+pyodbc://user:pass@dsn"
    #
    # ── 1-2  验证连接 ──
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 'SQLAlchemy 连接成功！' AS msg"))
        row = result.fetchone()
        print(f"\n✅ 连接测试: {row.msg}\n")

    # Engine 是"懒连接"的：只有真正执行语句时才打开数据库连接。
    # with engine.connect() 会在退出 with 块时自动关闭连接。

    return engine  # 返回给后续章节使用


# ═══════════════════════════════════════════════════════════════════════════════
# 第 2 章  事务与 DBAPI
# ═══════════════════════════════════════════════════════════════════════════════
def section_2(engine):
    print("\n" + "="*60)
    print("第 2 章：事务与 DBAPI")
    print("="*60)

    # ── 2-1  execute() + text() 执行原生 SQL ──
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS test_tx (x INT, y INT)"))
        conn.execute(
            text("INSERT INTO test_tx (x, y) VALUES (:x, :y)"),
            [{"x": 1, "y": 1}, {"x": 2, "y": 4}]   # 批量插入用列表
        )
        # ⚠️ 不调用 commit() 则事务会在 with 块结束时自动回滚
        conn.commit()   # 明确提交

    # ── 2-2  "begin once" 风格（推荐用于写操作）──
    with engine.begin() as conn:   # 自动提交或在异常时回滚
        conn.execute(text("INSERT INTO test_tx (x, y) VALUES (:x, :y)"),
                     [{"x": 3, "y": 9}])
    # with 块正常退出 → 自动 COMMIT；抛异常 → 自动 ROLLBACK

    # ── 2-3  查询结果的遍历方式 ──
    with engine.connect() as conn:
        result = conn.execute(text("SELECT x, y FROM test_tx ORDER BY x"))

        print("\n[方式 A] for row in result  （推荐）")
        for row in result:
            print(f"  x={row.x}, y={row.y}")

    
    # ── 2-4  绑定参数（防 SQL 注入的正确方式）──
    with engine.connect() as conn:
        x_val = 2
        result = conn.execute(
            text("SELECT x, y FROM test_tx WHERE x = :x"),
            {"x": x_val}        # ← 永远用 :name 占位符 + 字典传参
        )
        print(f"\n[绑定参数] x={x_val} 对应: {result.fetchone()}")


# ═══════════════════════════════════════════════════════════════════════════════
# 第 3 章  数据库元数据（Table / MetaData）
# ═══════════════════════════════════════════════════════════════════════════════
def section_3(engine):
    print("\n" + "="*60)
    print("第 3 章：数据库元数据")
    print("="*60)

    metadata = MetaData()   # 元数据容器，管理所有 Table 对象

    # ── 3-1  用 Core API 显式定义表结构 ──
    user_table = Table(
        "user_account",         # 表名
        metadata,               # 注册到 metadata
        Column("id",   Integer, primary_key=True),
        Column("name", String(30), nullable=False),
        Column("fullname", String(100)),
    )

    address_table = Table(
        "address",
        metadata,
        Column("id",      Integer, primary_key=True),
        Column("user_id", ForeignKey("user_account.id"), nullable=False),  # 外键
        Column("email",   String(200), nullable=False),
    )

    # ── 3-2  将所有表同步到数据库 ──
    metadata.create_all(engine)
    print("✅ 表已创建: user_account, address")

    # ── 3-3  通过属性访问列信息 ──
    print(f"\n[表信息] user_table.c 包含列: {[c.name for c in user_table.c]}")
    print(f"[外键]  address.user_id → {list(address_table.c.user_id.foreign_keys)}")

    # ── 3-4  从现有数据库反射（读取已有表结构）──
    # reflected_meta = MetaData()
    # reflected_meta.reflect(bind=engine)   # 自动发现数据库里的所有表
    # reflected_table = reflected_meta.tables["user_account"]

    return metadata, user_table, address_table


# ═══════════════════════════════════════════════════════════════════════════════
# 第 4 章  使用 ORM 映射类（推荐现代写法）
# ═══════════════════════════════════════════════════════════════════════════════

# ── 4-1  声明基类 ──
class Base(DeclarativeBase):
    pass
    # DeclarativeBase 会自动创建 MetaData，
    # 所有继承 Base 的类都共享同一个 metadata

# ── 4-2  定义 ORM 模型 ──
class User(Base):
    __tablename__ = "user_account"

    # Mapped[int] 告诉类型检查器列的 Python 类型
    id:       Mapped[int]           = mapped_column(primary_key=True)
    name:     Mapped[str]           = mapped_column(String(30))
    fullname: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 关系声明（详见第 8 章）
    addresses: Mapped[List["Address"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r}>"


class Address(Base):
    __tablename__ = "address"

    id:      Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    email:   Mapped[str] = mapped_column(String(200))

    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address id={self.id} email={self.email!r}>"


def section_4(engine):
    print("\n" + "="*60)
    print("第 4 章：ORM 映射类")
    print("="*60)

    # 将 ORM 类对应的表同步到数据库
    # checkfirst=True → 表已存在则跳过，不会报错
    Base.metadata.create_all(engine, checkfirst=True)
    print("✅ ORM 表已就绪")

    # 查看 ORM 类对应的 Table 对象
    print(f"\nUser.__table__ 列: {[c.name for c in User.__table__.c]}")


# ═══════════════════════════════════════════════════════════════════════════════
# 第 5 章  Core 方式增删改查
# ═══════════════════════════════════════════════════════════════════════════════
def section_5(engine, user_table, address_table):
    print("\n" + "="*60)
    print("第 5 章：Core 方式增删改查")
    print("="*60)

    # ── 5-1  INSERT ──
    with engine.begin() as conn:
        stmt = insert(user_table).values(
            name="spongebob", fullname="Spongebob Squarepants"
        )
        result = conn.execute(stmt)
        print(f"[INSERT] 新增行 id: {result.inserted_primary_key}")

        # 批量插入
        conn.execute(
            insert(user_table),
            [
                {"name": "sandy",   "fullname": "Sandy Cheeks"},
                {"name": "patrick", "fullname": "Patrick Star"},
            ]
        )

    # ── 5-2  SELECT ──
    with engine.connect() as conn:
        stmt = select(user_table).where(user_table.c.name.in_(["spongebob", "sandy"]))
        result = conn.execute(stmt)
        print("\n[SELECT]")
        for row in result:
            print(f"  {row}")

        # 只选择部分列
        stmt2 = select(user_table.c.name, user_table.c.fullname)
        for row in conn.execute(stmt2):
            print(f"  name={row.name}")

    # ── 5-3  UPDATE ──
    with engine.begin() as conn:
        stmt = (
            update(user_table)
            .where(user_table.c.name == "patrick")
            .values(fullname="Patrick Star (Updated)")
        )
        conn.execute(stmt)
        print("\n[UPDATE] patrick 的 fullname 已更新")

    # ── 5-4  DELETE ──
    with engine.begin() as conn:
        stmt = delete(user_table).where(user_table.c.name == "patrick")
        result = conn.execute(stmt)
        print(f"\n[DELETE] 删除了 {result.rowcount} 行")


# ═══════════════════════════════════════════════════════════════════════════════
# 第 6 章  ORM 方式增删改查（Session）
# ═══════════════════════════════════════════════════════════════════════════════
def section_6(engine):
    print("\n" + "="*60)
    print("第 6 章：ORM Session 增删改查")
    print("="*60)

    # ── 6-1  新增对象 ──
    with Session(engine) as session:
        # 方式 A：直接构造并 add
        u1 = User(name="squidward", fullname="Squidward Q. Tentacles")
        u2 = User(name="krabs",     fullname="Eugene H. Krabs")
        session.add(u1)
        session.add(u2)
        # 或者批量: session.add_all([u1, u2])

        session.flush()   # 把 SQL 发送到数据库但不提交（可以获取 id）
        print(f"[ADD] squidward id={u1.id}, krabs id={u2.id}")

        session.commit()  # 正式提交

    # ── 6-2  查询 ──
    with Session(engine) as session:
        # 查单个：get by primary key
        user = session.get(User, 1)   # 等价于 SELECT WHERE id=1
        if user:
            print(f"\n[GET]  id=1 → {user}")

        # 查多个：select()
        stmt = select(User).where(User.name.like("%a%"))
        users = session.scalars(stmt).all()
        print(f"\n[scalars] name 含 'a': {users}")

    # ── 6-3  修改对象（identity map 自动追踪） ──
    with Session(engine) as session:
        user = session.get(User, 2)
        if user:
            user.fullname = "Sandy Cheeks (Dr.)"   # 直接赋值，ORM 会追踪变化
            session.commit()
            print(f"\n[UPDATE via ORM] {user}")

    # ── 6-4  删除对象 ──
    with Session(engine) as session:
        user = session.get(User, 2)
        if user:
            session.delete(user)
            session.commit()
            print(f"\n[DELETE via ORM] id=2 已删除")


# ═══════════════════════════════════════════════════════════════════════════════
# 第 7 章  使用 select() 查询（进阶）
# ═══════════════════════════════════════════════════════════════════════════════
def section_7(engine, user_table):
    print("\n" + "="*60)
    print("第 7 章：select() 进阶查询")
    print("="*60)

    with Session(engine) as session:

        # ── 7-1  WHERE 子句 ──
        stmt = select(User).where(
            and_(
                User.name != "squidward",
                User.fullname.is_not(None)
            )
        )
        print("[WHERE and_]", session.scalars(stmt).all())

        # ── 7-2  ORDER BY / LIMIT / OFFSET ──
        stmt = (
            select(User)
            .order_by(desc(User.name))
            .limit(5)
            .offset(0)
        )
        print("\n[ORDER BY desc]", session.scalars(stmt).all())

        # ── 7-3  聚合函数 ──
        with engine.connect() as conn:
            result = conn.execute(select(func.count(user_table.c.id)))
            print(f"\n[COUNT] user_account 共 {result.scalar()} 条")

        # ── 7-4  子查询 ──
        subq = select(User.id).where(User.name == "spongebob").scalar_subquery()
        stmt = select(User).where(User.id == subq)
        print("\n[子查询]", session.scalars(stmt).all())

        # ── 7-5  scalars() vs all() vs one() vs first() ──
        #   scalars()     → 返回 ScalarResult，迭代得到 ORM 对象（或第一列的值）
        #   .all()        → list
        #   .one()        → 恰好一行，否则抛异常
        #   .one_or_none()→ 0 或 1 行
        #   .first()      → 第一行 or None


# ═══════════════════════════════════════════════════════════════════════════════
# 第 8 章  关系（relationship）与 JOIN
# ═══════════════════════════════════════════════════════════════════════════════
def section_8(engine):
    print("\n" + "="*60)
    print("第 8 章：关系与 JOIN")
    print("="*60)

    # ── 8-1  准备数据 ──
    with Session(engine) as session:
        # 重新插入 spongebob（之前可能已存在，这里用 merge 避免重复键冲突）
        spongebob = session.get(User, 1)
        if not spongebob:
            spongebob = User(name="spongebob", fullname="Spongebob Squarepants")
            session.add(spongebob)
            session.flush()

        # 关联地址（通过关系直接赋值）
        addr1 = Address(email="sponge@example.com", user=spongebob)
        addr2 = Address(email="bob@bikini.bottom",  user=spongebob)
        session.add_all([addr1, addr2])
        session.commit()
        print(f"[关系] spongebob 的地址: {spongebob.addresses}")

    # ── 8-2  显式 JOIN ──
    with Session(engine) as session:
        stmt = (
            select(User, Address)
            .join(Address, User.id == Address.user_id)
            .where(Address.email.contains("example"))
        )
        for user, addr in session.execute(stmt):
            print(f"\n[JOIN] User={user.name}, Email={addr.email}")

    # ── 8-3  利用 relationship 自动 JOIN ──
    with Session(engine) as session:
        stmt = select(User).join(User.addresses)
        users = session.scalars(stmt).unique().all()
        print(f"\n[relationship JOIN] 有地址的用户: {users}")

    # ── 8-4  懒加载 vs 预加载 ──
    #   懒加载（默认）: 访问 user.addresses 时触发额外 SELECT
    #   预加载方式:
    from sqlalchemy.orm import selectinload, joinedload
    with Session(engine) as session:
        stmt = select(User).options(selectinload(User.addresses))
        # selectinload: 额外发一条 SELECT ... WHERE user_id IN (...)
        # joinedload:   在主查询里做 LEFT OUTER JOIN
        users = session.scalars(stmt).all()
        for u in users:
            print(f"\n[selectinload] {u.name} → {u.addresses}")


# ═══════════════════════════════════════════════════════════════════════════════
# 第 9 章  更新与删除（ORM 风格）
# ═══════════════════════════════════════════════════════════════════════════════
def section_9(engine):
    print("\n" + "="*60)
    print("第 9 章：ORM 更新与删除")
    print("="*60)

    # ── 9-1  批量 UPDATE（ORM-enabled update）──
    with Session(engine) as session:
        stmt = (
            update(User)
            .where(User.name == "squidward")
            .values(fullname="Squidward Tentacles (Updated)")
        )
        result = session.execute(stmt)
        session.commit()
        print(f"[bulk UPDATE] 影响 {result.rowcount} 行")

    # ── 9-2  批量 DELETE（ORM-enabled delete）──
    with Session(engine) as session:
        stmt = delete(Address).where(Address.email.like("%bikini%"))
        result = session.execute(stmt)
        session.commit()
        print(f"[bulk DELETE] 删除了 {result.rowcount} 个地址")

    # ── 9-3  级联删除 ──
    # 在 relationship() 里加 cascade="all, delete-orphan"
    # 则删除 User 时，其关联的 Address 自动被删除
    # class User(Base):
    #     addresses = relationship("Address", cascade="all, delete-orphan")


# ═══════════════════════════════════════════════════════════════════════════════
# 第 10 章  综合示例：博客系统
# ═══════════════════════════════════════════════════════════════════════════════

class BlogBase(DeclarativeBase):
    pass

class Author(BlogBase):
    __tablename__ = "blog_author"
    id:    Mapped[int] = mapped_column(primary_key=True)
    name:  Mapped[str] = mapped_column(String(50))
    posts: Mapped[List["Post"]] = relationship(back_populates="author",
                                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Author {self.name!r}>"

class Post(BlogBase):
    __tablename__ = "blog_post"
    id:        Mapped[int] = mapped_column(primary_key=True)
    title:     Mapped[str] = mapped_column(String(200))
    content:   Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("blog_author.id"))
    author:    Mapped["Author"] = relationship(back_populates="posts")

    def __repr__(self):
        return f"<Post {self.title!r}>"

def section_10(engine):
    print("\n" + "="*60)
    print("第 10 章：综合示例 —— 博客系统")
    print("="*60)

    BlogBase.metadata.create_all(engine, checkfirst=True)

    # ── 创建作者和文章 ──
    with Session(engine) as session:
        alice = Author(name="Alice")
        bob   = Author(name="Bob")
        session.add_all([alice, bob])
        session.flush()

        posts = [
            Post(title="SQLAlchemy 入门",  content="Core 与 ORM ...", author=alice),
            Post(title="Python 异步编程",   content="asyncio ...",     author=alice),
            Post(title="数据库设计原则",    content="范式 ...",         author=bob),
        ]
        session.add_all(posts)
        session.commit()
        print("✅ 博客数据已创建")

    # ── 查询：某作者的所有文章 ──
    with Session(engine) as session:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Author)
            .where(Author.name == "Alice")
            .options(selectinload(Author.posts))
        )
        alice = session.scalars(stmt).first()
        print(f"\n[{alice}] 的文章:")
        for post in alice.posts:
            print(f"  - {post.title}")

    # ── 统计：每位作者的文章数 ──
    with Session(engine) as session:
        stmt = (
            select(Author.name, func.count(Post.id).label("post_count"))
            .join(Post, Author.id == Post.author_id)
            .group_by(Author.id)
            .order_by(desc("post_count"))
        )
        print("\n[统计] 作者文章数:")
        for row in session.execute(stmt):
            print(f"  {row.name}: {row.post_count} 篇")

    # ── 搜索标题关键词 ──
    with Session(engine) as session:
        keyword = "Python"
        stmt = select(Post).where(Post.title.contains(keyword))
        results = session.scalars(stmt).all()
        print(f"\n[搜索] 标题含 '{keyword}': {results}")

    # ── 删除作者（级联删除其文章）──
    with Session(engine) as session:
        bob = session.scalars(select(Author).where(Author.name == "Bob")).first()
        if bob:
            session.delete(bob)
            session.commit()
            print("\n[级联删除] Bob 及其所有文章已删除")


# ═══════════════════════════════════════════════════════════════════════════════
# 主程序入口
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("╔══════════════════════════════════════════════╗")
    print("║     SQLAlchemy 2.0 Tutorial  开始运行        ║")
    print("╚══════════════════════════════════════════════╝")

    # 所有章节共用一个内存数据库引擎
    engine = create_engine("sqlite+pysqlite:///:memory:", echo=False)
    # 提示：改 echo=True 可以看到所有生成的 SQL 语句

    # ── 按顺序执行各章节 ──
    section_1()                                       # 第 1 章
    section_2(engine)                                 # 第 2 章

    metadata, user_table, address_table = section_3(engine)   # 第 3 章
    section_4(engine)                                 # 第 4 章（重新建 ORM 表）
    section_5(engine, user_table, address_table)      # 第 5 章
    section_6(engine)                                 # 第 6 章
    section_7(engine, user_table)                     # 第 7 章
    section_8(engine)                                 # 第 8 章
    section_9(engine)                                 # 第 9 章
    section_10(engine)                                # 第 10 章

    print("\n\n✅  所有章节执行完毕！")
    print("━"*50)
    print("💡 提示：")
    print("  • 修改 echo=False → echo=True 可查看完整 SQL")
    print("  • 每个 section_X() 函数可以单独调用")
    print("  • 将 sqlite:///:memory: 改为实际数据库 URL 可连接真实数据库")


if __name__ == "__main__":
    main()