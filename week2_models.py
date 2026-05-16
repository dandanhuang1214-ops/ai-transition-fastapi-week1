"""
第二周 数据库模型定义
====================
使用 SQLModel（基于 SQLAlchemy 2.0 + Pydantic）定义 RAG 知识库的核心表。

表结构设计思路：
    documents（文档表）
    ├── 存储原始文档的元信息和全文
    │
    chunks（文本块表）
    ├── 将长文档切分成小块，每个块关联到源文档
    │
    conversations（会话表）
    ├── 记录用户的多轮问答会话
    │
    messages（消息表）
    └── 记录每个会话中的问答消息对

为什么要把 documents 和 chunks 分开？
    1. 检索粒度：检索时不需要返回整篇文档，只需返回最相关的几个块
    2. 上下文窗口：大模型有 token 限制，不能塞入整篇文档
    3. 精准引用：可以精确指出答案来自文档的哪个段落
    4. 独立管理：更新文档时只需重新切分，不影响其他文档
"""

from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import Field, Session, SQLModel, create_engine, Relationship

# ============================================================
# Document 表 — 存储原始文档
# ============================================================
class DocumentBase(SQLModel):
    """文档的基础字段（用于创建和查询）"""
    title: str = Field(
        max_length=200,
        description="文档标题，例如《FastAPI 官方教程笔记》"
    )
    content: str = Field(
        description="文档的完整文本内容"
    )
    file_type: str = Field(
        default="txt",
        max_length=20,
        description="文档类型：txt / markdown / pdf_text 等"
    )


class Document(DocumentBase, table=True):
    """文档的数据库表模型"""
    __tablename__ = "documents"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="自增主键，由数据库自动生成"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="文档上传时间（UTC）"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="最后更新时间（UTC）"
    )

    # 一对多关系：一个文档可以有多个文本块
    # back_populates 让 Chunk.doc 也可以反向访问到 Document
    chunks: List["Chunk"] = Relationship(back_populates="doc")


class DocumentPublic(DocumentBase):
    """返回给前端的文档模型（包含 id 和时间，不含 chunks 详情）"""
    id: int
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0  # 该文档被切分成了多少块


class DocumentCreate(DocumentBase):
    """创建文档时的请求体模型"""
    pass


class DocumentUpdate(SQLModel):
    """更新文档时的请求体模型（所有字段可选）"""
    title: Optional[str] = None
    content: Optional[str] = None
    file_type: Optional[str] = None


# ============================================================
# Chunk 表 — 存储文档切分后的文本块
# ============================================================
class ChunkBase(SQLModel):
    """文本块的基础字段"""
    chunk_text: str = Field(description="该块的文本内容")
    chunk_index: int = Field(description="该块在原文档中的序号（从 0 开始）")
    doc_id: int = Field(
        foreign_key="documents.id",
        description="所属文档的 ID，外键关联 documents 表"
    )


class Chunk(ChunkBase, table=True):
    """文本块的数据库表模型"""
    __tablename__ = "chunks"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 多对一反向关系：通过 chunk.doc 可以访问所属的 Document
    doc: Document = Relationship(back_populates="chunks")


class ChunkPublic(ChunkBase):
    """返回给前端的文本块模型"""
    id: int
    created_at: datetime


# ============================================================
# Conversation 表 — 存储问答会话
# ============================================================
class ConversationBase(SQLModel):
    """会话的基础字段"""
    title: str = Field(
        default="新会话",
        max_length=200,
        description="会话标题，便于回顾"
    )


class Conversation(ConversationBase, table=True):
    """会话的数据库表模型"""
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 一对多：一个会话包含多条消息
    messages: List["Message"] = Relationship(back_populates="conversation")


class ConversationPublic(ConversationBase):
    """返回给前端的会话模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationCreate(ConversationBase):
    """创建会话时的请求体"""
    pass


# ============================================================
# Message 表 — 存储会话中的每条消息
# ============================================================
class MessageBase(SQLModel):
    """消息的基础字段"""
    role: str = Field(
        max_length=20,
        description="消息角色：user（用户）或 assistant（助手）"
    )
    content: str = Field(description="消息文本内容")
    conversation_id: int = Field(
        foreign_key="conversations.id",
        description="所属会话 ID"
    )


class Message(MessageBase, table=True):
    """消息的数据库表模型"""
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 多对一反向关系
    conversation: Conversation = Relationship(back_populates="messages")


class MessagePublic(MessageBase):
    """返回给前端的消息模型"""
    id: int
    created_at: datetime


class MessageCreate(SQLModel):
    """创建消息时的请求体"""
    role: str = "user"
    content: str


# ============================================================
# 数据库引擎和工具函数
# ============================================================
# 使用 week2_config 中的数据库路径
from week2_config import DATABASE_URL, DATABASE_CONNECT_ARGS

engine = create_engine(DATABASE_URL, connect_args=DATABASE_CONNECT_ARGS)


def create_db_and_tables():
    """根据所有 SQLModel 表模型，在数据库中创建对应的表。
    如果表已存在则跳过（不重复创建）。
    通常在 FastAPI 的 startup 事件中调用一次。
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """获取数据库会话的依赖注入函数。
    每次请求自动创建新的 Session，请求结束后自动关闭。
    用法：
        SessionDep = Annotated[Session, Depends(get_session)]

        然后在路由函数参数中使用：
        def create_doc(doc: DocumentCreate, session: SessionDep) -> DocumentPublic:
            ...
    """
    with Session(engine) as session:
        yield session
