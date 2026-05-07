import sqlite3  # 导入 SQLite 数据库模块

# 连接到 SQLite 数据库文件，如果不存在会自动创建
con = sqlite3.connect("apple.db")
# 创建游标对象，用于执行 SQL 语句
cur = con.cursor()

# 执行 SQL 语句创建表（如果表不存在）
cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
)
""")

# 插入一条数据到 items 表
cur.execute(
    "INSERT INTO items (name, price) VALUES (?, ?)",  # 使用占位符防止 SQL 注入
    ("apple", 12.5),  # 插入苹果的价格
)

# 提交事务，将插入的数据保存到数据库
con.commit()

# 查询所有数据
res = cur.execute("SELECT id, name, price FROM items")
# 获取查询结果的所有行
items = res.fetchall()

# 关闭数据库连接
con.close()

# 打印查询结果
print(items)
