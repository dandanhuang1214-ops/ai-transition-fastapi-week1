"""
第二周 FastAPI 文档管理 API
===========================
提供文档 CRUD、文本切分、会话管理、消息记录等接口。

启动方式：
    fastapi dev week2_doc_api.py

    或者：
    uvicorn week2_doc_api:app --reload --port 8000

启动后访问 http://127.0.0.1:8000/docs 可以查看和测试所有接口。

注意：此服务启动后，再用 Streamlit 调用它（见 week2_streamlit_app.py）。
"""

from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, select, func

# 导入我们的模型和配置
from week2_models import (
    # 数据库工具
    engine, create_db_and_tables, get_session,
    # Document 相关模型
    Document, DocumentPublic, DocumentCreate, DocumentUpdate,
    # Chunk 相关模型
    Chunk, ChunkPublic,
    # Conversation 相关模型
    Conversation, ConversationPublic, ConversationCreate,
    # Message 相关模型
    Message, MessagePublic, MessageCreate,
)
from week2_config import (
    APP_TITLE, APP_VERSION, APP_DESCRIPTION,
    CHUNK_SIZE, CHUNK_OVERLAP,
)

# 定义 SessionDep 类型：FastAPI 依赖注入的数据库会话
SessionDep = Annotated[Session, Depends(get_session)]

# ============================================================
# FastAPI 应用实例
# ============================================================
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)


# ============================================================
# 启动事件：创建数据库表
# ============================================================
@app.on_event("startup")
def on_startup():
    """FastAPI 启动时自动创建所有数据库表（如果不存在的话）。
    这是 FastAPI 的生命周期事件，比 @app.get 装饰的函数更早执行。
    """
    create_db_and_tables()


# ============================================================
# 工具函数：文本切分
# ============================================================
def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE,
                           chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """将长文本按字符数切分成多个块。

    参数:
        text: 要切分的原始文本
        chunk_size: 每个块的最大字符数
        chunk_overlap: 相邻块之间的重叠字符数

    返回:
        字符串列表，每个元素是一个文本块

    切分策略说明:
        使用字符级固定长度切分。这是最简单的切分方式，后续可以升级为
        按段落切分、按标题切分、语义切分等更高级的方式。

    重叠的作用:
        假设有一句话 "Python 是一门很好的编程语言"，
        如果 chunk_size=6, chunk_overlap=0：
            块1: "Python 是一门很"
            块2: "好的编程语言"
        此时 "很好" 被拆开了，检索时可能匹配不到。

        如果 chunk_overlap=2：
            块1: "Python 是一门很"
            块2: "一门很好的编程"
            块3: "的编程语言"
        重叠让关键信息更大概率落在某一块的内部。

    示例:
        >>> chunks = split_text_into_chunks("A" * 1000, chunk_size=500, chunk_overlap=50)
        >>> len(chunks)
        3
    """
    if not text or chunk_size <= 0:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk_text = text[start:end]
        chunks.append(chunk_text)
        # 下一块的起点 = 当前起点 + chunk_size - chunk_overlap
        start += chunk_size - chunk_overlap

    return chunks


# ============================================================
# 根路径 + 健康检查
# ============================================================
@app.get("/")
async def root():
    """根路径：返回 API 基本信息"""
    return {
        "app": APP_TITLE,
        "version": APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查接口：用于确认服务是否正常运行"""
    return {"status": "ok", "service": APP_TITLE}


# ============================================================
# 文档 CRUD 接口
# ============================================================

@app.post("/documents/", response_model=DocumentPublic)
def create_document(doc_in: DocumentCreate, session: SessionDep):
    """创建文档并自动切分为文本块。

    工作流程：
        1. 将文档元信息和全文存入 documents 表
        2. 调用 split_text_into_chunks() 将内容切分成块
        3. 批量创建 Chunk 记录，关联到刚创建的文档

    请求体示例：
        {
            "title": "FastAPI 入门笔记",
            "content": "FastAPI 是一个现代 Web 框架...(长文本)",
            "file_type": "markdown"
        }

    返回: 文档信息 + 被切分成了多少块
    """
    # Step 1: 创建文档记录
    db_doc = Document.model_validate(doc_in)
    session.add(db_doc)
    session.commit()
    session.refresh(db_doc)  # 刷新以获取数据库生成的 id

    # Step 2: 切分文档内容
    chunk_texts = split_text_into_chunks(doc_in.content)

    # Step 3: 批量创建 Chunk 记录
    for i, chunk_text in enumerate(chunk_texts):
        chunk = Chunk(
            chunk_text=chunk_text,
            chunk_index=i,
            doc_id=db_doc.id,
        )
        session.add(chunk)

    session.commit()

    # 构建返回对象（包含块数量）
    return DocumentPublic(
        id=db_doc.id,
        title=db_doc.title,
        content=db_doc.content,
        file_type=db_doc.file_type,
        created_at=db_doc.created_at,
        updated_at=db_doc.updated_at,
        chunk_count=len(chunk_texts),
    )


@app.get("/documents/", response_model=List[DocumentPublic])
def list_documents(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0, description="跳过的记录数")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="返回的最大记录数")] = 20,
):
    """获取文档列表（支持分页）。

    查询参数:
        offset: 从第几条开始（默认 0）
        limit: 最多返回多少条（默认 20，最大 100）

    示例 URL:
        GET /documents/              → 获取前 20 条
        GET /documents/?offset=5    → 跳过前 5 条，获取第 6-25 条
        GET /documents/?limit=50    → 获取前 50 条
    """
    docs = session.exec(
        select(Document).offset(offset).limit(limit)
    ).all()

    # 为每个文档查询它有多少个 chunk
    result = []
    for doc in docs:
        chunk_count = session.exec(
            select(func.count(Chunk.id)).where(Chunk.doc_id == doc.id)
        ).one()
        result.append(DocumentPublic(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            file_type=doc.file_type,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            chunk_count=chunk_count,
        ))
    return result


@app.get("/documents/{doc_id}", response_model=DocumentPublic)
def get_document(doc_id: int, session: SessionDep):
    """获取单个文档的详细信息。

    路径参数:
        doc_id: 文档 ID

    示例: GET /documents/1
    """
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    # 查询该文档有多少个 chunk
    chunk_count = session.exec(
        select(func.count(Chunk.id)).where(Chunk.doc_id == doc_id)
    ).one()

    return DocumentPublic(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        file_type=doc.file_type,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunk_count=chunk_count,
    )


@app.get("/documents/{doc_id}/chunks", response_model=List[ChunkPublic])
def get_document_chunks(
    doc_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=50)] = 20,
):
    """获取某个文档的所有文本块（支持分页）。

    这是 RAG 调试的关键接口：可以检查每篇文档被切成了哪些块，
    判断切分策略是否合理。
    """
    # 先确认文档存在
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    chunks = session.exec(
        select(Chunk)
        .where(Chunk.doc_id == doc_id)
        .order_by(Chunk.chunk_index)  # 按块序号排序
        .offset(offset)
        .limit(limit)
    ).all()
    return chunks


@app.patch("/documents/{doc_id}", response_model=DocumentPublic)
def update_document(doc_id: int, doc_update: DocumentUpdate, session: SessionDep):
    """部分更新文档。

    如果更新了 content 字段，会删除旧的文本块并重新切分。

    请求体示例:
        {"title": "新标题"}
        {"content": "全新的文档内容..."}
    """
    db_doc = session.get(Document, doc_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    # 只更新用户实际传入的字段
    update_data = doc_update.model_dump(exclude_unset=True)
    db_doc.sqlmodel_update(update_data)

    # 如果内容被更新了，删除旧 chunks 并重新切分
    if "content" in update_data:
        # 删除旧的所有 chunks
        old_chunks = session.exec(
            select(Chunk).where(Chunk.doc_id == doc_id)
        ).all()
        for chunk in old_chunks:
            session.delete(chunk)

        # 重新切分并创建新的 chunks
        new_chunk_texts = split_text_into_chunks(update_data["content"])
        for i, chunk_text in enumerate(new_chunk_texts):
            session.add(Chunk(
                chunk_text=chunk_text,
                chunk_index=i,
                doc_id=doc_id,
            ))

    session.add(db_doc)
    session.commit()
    session.refresh(db_doc)

    # 查询最终的 chunk 数量
    chunk_count = session.exec(
        select(func.count(Chunk.id)).where(Chunk.doc_id == doc_id)
    ).one()

    return DocumentPublic(
        id=db_doc.id,
        title=db_doc.title,
        content=db_doc.content,
        file_type=db_doc.file_type,
        created_at=db_doc.created_at,
        updated_at=db_doc.updated_at,
        chunk_count=chunk_count,
    )


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, session: SessionDep):
    """删除文档及其所有关联的文本块。

    返回: {"ok": true, "message": "..."}
    """
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    # 删除关联的 chunks（SQLite 不自动级联删除，需要手动处理）
    chunks = session.exec(
        select(Chunk).where(Chunk.doc_id == doc_id)
    ).all()
    for chunk in chunks:
        session.delete(chunk)

    # 删除文档本身
    session.delete(doc)
    session.commit()
    return {"ok": True, "message": f"文档 {doc_id} 及其 {len(chunks)} 个文本块已删除"}


# ============================================================
# 会话 CRUD 接口
# ============================================================

@app.post("/conversations/", response_model=ConversationPublic)
def create_conversation(conv_in: ConversationCreate, session: SessionDep):
    """创建新会话"""
    db_conv = Conversation.model_validate(conv_in)
    session.add(db_conv)
    session.commit()
    session.refresh(db_conv)
    return ConversationPublic(
        id=db_conv.id,
        title=db_conv.title,
        created_at=db_conv.created_at,
        updated_at=db_conv.updated_at,
        message_count=0,
    )


@app.get("/conversations/", response_model=List[ConversationPublic])
def list_conversations(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=50)] = 20,
):
    """获取会话列表"""
    convs = session.exec(
        select(Conversation).offset(offset).limit(limit)
    ).all()

    result = []
    for conv in convs:
        msg_count = session.exec(
            select(func.count(Message.id))
            .where(Message.conversation_id == conv.id)
        ).one()
        result.append(ConversationPublic(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count,
        ))
    return result


# ============================================================
# 消息接口
# ============================================================

@app.post("/conversations/{conv_id}/messages/", response_model=MessagePublic)
def add_message(conv_id: int, msg_in: MessageCreate, session: SessionDep):
    """向会话中添加一条消息"""
    conv = session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")

    db_msg = Message(
        role=msg_in.role,
        content=msg_in.content,
        conversation_id=conv_id,
    )
    session.add(db_msg)
    session.commit()
    session.refresh(db_msg)
    return db_msg


@app.get("/conversations/{conv_id}/messages/", response_model=List[MessagePublic])
def list_messages(conv_id: int, session: SessionDep):
    """获取某个会话的所有消息（按时间排序）"""
    conv = session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")

    return session.exec(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    ).all()


# ============================================================
# 统计接口：方便查看数据库概况
# ============================================================

@app.get("/stats/")
def get_stats(session: SessionDep):
    """获取数据库各表的统计信息。
    Streamlit 的"数据库概览"页面会调用这个接口。
    """
    return {
        "document_count": session.exec(select(func.count(Document.id))).one(),
        "chunk_count": session.exec(select(func.count(Chunk.id))).one(),
        "conversation_count": session.exec(select(func.count(Conversation.id))).one(),
        "message_count": session.exec(select(func.count(Message.id))).one(),
    }
