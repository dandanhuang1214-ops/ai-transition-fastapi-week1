"""
第二周 Streamlit 前端应用
=========================
通过 Streamlit 调用 FastAPI 后端，实现文档管理、查看、问答界面。

这是 Week 2 的核心验收项目：把"后端 API + 数据库 + 前端界面"串起来。

启动方式（需要同时运行两个终端）：
    终端 1（后端）:
        fastapi dev week2_doc_api.py

    终端 2（前端）:
        streamlit run week2_streamlit_app.py

知识点覆盖：
    - session_state：页面间共享状态（计数器、通知消息）
    - st.form + 回调函数：带验证的表单提交
    - requests 库调用 REST API：GET / POST / DELETE 请求
    - 侧边栏导航：多页面切换
    - 数据展示：表格、JSON、统计卡片
    - 错误处理：try/except 包裹 API 调用
"""

import streamlit as st
import requests
import datetime
from typing import Optional

# 导入配置
from week2_config import API_BASE_URL

# ============================================================
# 页面配置（必须是第一个 Streamlit 命令）
# ============================================================
st.set_page_config(
    page_title="个人知识库系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 全局状态初始化（session_state 用法）
# ============================================================
# session_state 是 Streamlit 的"跨重新运行"存储机制。
#
# 关键概念：
#   Streamlit 每次用户交互（点击、输入）都会从上到下重新运行整个脚本。
#   普通变量会在重新运行时被重置，但 session_state 中的值会保留。
#
# 常见用法：
#   st.session_state.key        → 读取
#   st.session_state.key = val  → 写入
#   if "key" not in st.session_state → 初始化检查
#
# 下面的代码只在 app 首次加载时执行一次，后续重新运行时跳过。

if "current_page" not in st.session_state:
    # 当前选中的页面（侧边栏导航用）
    st.session_state.current_page = "📄 文档管理"

if "notification" not in st.session_state:
    # 全局通知消息，格式：(消息文本, 消息类型)
    # 消息类型：success / error / info / warning
    # 任何页面都可以设置此消息，显示后自动清除
    st.session_state.notification = None

if "api_connected" not in st.session_state:
    # 后端 API 连接状态：None=未检测, True=已连接, False=连接失败
    st.session_state.api_connected = None


# ============================================================
# 工具函数
# ============================================================

def check_api_connection() -> bool:
    """检测后端 FastAPI 是否在运行。
    调用 /health 接口，如果能正常返回 200 则说明后端在线。
    结果同时缓存到 session_state.api_connected 中。
    """
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=3)
        st.session_state.api_connected = resp.status_code == 200
        return st.session_state.api_connected
    except requests.exceptions.ConnectionError:
        # 连接被拒绝 → 后端没有启动
        st.session_state.api_connected = False
        return False
    except Exception:
        st.session_state.api_connected = False
        return False


def show_notification():
    """显示并自动清除全局通知。
    在页面顶部调用，确保用户能看到操作反馈。
    显示后立即置 None，避免每次重新运行都重复显示。
    """
    if st.session_state.notification:
        msg, msg_type = st.session_state.notification
        if msg_type == "success":
            st.success(msg)
        elif msg_type == "error":
            st.error(msg)
        elif msg_type == "warning":
            st.warning(msg)
        else:
            st.info(msg)
        st.session_state.notification = None  # 显示后清除


def api_get(endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
    """封装 GET 请求，统一错误处理。
    所有从 Streamlit 到 FastAPI 的 GET 请求都通过这个函数，
    避免在页面代码中重复写 try/except。
    """
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=10)
        resp.raise_for_status()  # 4xx/5xx 自动抛出 HTTPError
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.session_state.notification = ("❌ 无法连接后端，请确认 week2_doc_api.py 已启动", "error")
        return None
    except Exception as e:
        st.session_state.notification = (f"❌ API 请求失败: {e}", "error")
        return None


def api_post(endpoint: str, data: dict) -> Optional[dict]:
    """封装 POST 请求，统一错误处理"""
    try:
        resp = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.session_state.notification = ("❌ 无法连接后端", "error")
        return None
    except requests.exceptions.HTTPError as e:
        # 422 等业务错误，把后端返回的 detail 展示出来
        detail = resp.text if 'resp' in dir() else str(e)
        st.session_state.notification = (f"❌ 请求失败: {detail}", "error")
        return None
    except Exception as e:
        st.session_state.notification = (f"❌ 请求失败: {e}", "error")
        return None


def api_delete(endpoint: str) -> Optional[dict]:
    """封装 DELETE 请求，统一错误处理"""
    try:
        resp = requests.delete(f"{API_BASE_URL}{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.session_state.notification = ("❌ 无法连接后端", "error")
        return None
    except Exception as e:
        st.session_state.notification = (f"❌ 请求失败: {e}", "error")
        return None


# ============================================================
# 侧边栏：导航 + 连接状态
# ============================================================

with st.sidebar:
    st.title("📚 个人知识库")
    st.caption("Week 2 实践项目")

    st.divider()

    # ---- 导航菜单 ----
    # 使用 radio 实现页面切换。选中的值存入 session_state.current_page。
    # key 参数确保 radio 的状态在重新运行时保留。
    page = st.radio(
        "导航",
        options=[
            "📄 文档管理",
            "🔍 文档详情",
            "💬 智能问答",
            "📊 数据库概览",
        ],
        key="nav_radio",
        # 将当前选中的页面同步回 session_state
        index=[
            "📄 文档管理",
            "🔍 文档详情",
            "💬 智能问答",
            "📊 数据库概览",
        ].index(st.session_state.current_page),
    )
    # 当用户切换 radio 时，更新 current_page
    st.session_state.current_page = page

    st.divider()

    # ---- 后端连接状态显示 ----
    st.subheader("🔗 后端状态")

    # 检测连接按钮，on_click 回调函数
    # 注意：st.button 不支持 on_click（这是后面版本的特性），
    # 所以这里用 if st.button 模式
    if st.button("🔍 检测连接", use_container_width=True):
        check_api_connection()

    # 根据连接状态显示不同指示
    if st.session_state.api_connected is True:
        st.success("✅ 后端已连接")
    elif st.session_state.api_connected is False:
        st.error("❌ 后端未连接")
        st.caption("请在终端运行：")
        st.code("fastapi dev week2_doc_api.py", language="bash")
    else:
        st.info("⚪ 尚未检测")

    st.divider()
    st.caption(f"API 地址: {API_BASE_URL}")
    st.caption(f"启动时间: {datetime.datetime.now().strftime('%H:%M:%S')}")


# ============================================================
# 页面主体：根据导航切换内容
# ============================================================

# 显示全局通知
show_notification()

# 每次页面加载时自动检测连接（静默，不打断用户）
if st.session_state.api_connected is None:
    check_api_connection()

# ============================================================
# 页面 1：📄 文档管理（默认页面）
# ============================================================
if st.session_state.current_page == "📄 文档管理":
    st.title("📄 文档管理")
    st.caption("上传文档 → 自动切分为文本块 → 存入数据库")

    # ---- 左侧：上传表单  |  右侧：文档列表 ----
    col_left, col_right = st.columns([2, 3])

    with col_left:
        st.subheader("➕ 新增文档")

        # st.form 的作用：
        #   1. 将多个输入组件合并为一个逻辑组
        #   2. 只有点击提交按钮才会触发重新运行（而非每次输入都触发）
        #   3. 配合 on_click 回调函数处理提交逻辑
        #
        # clear_on_submit=True 表示提交后清空表单内容
        with st.form(key="doc_form", clear_on_submit=True):
            doc_title = st.text_input(
                "文档标题",
                placeholder="例如：FastAPI 官方教程笔记",
                max_chars=200,
            )
            doc_type = st.selectbox(
                "文档类型",
                options=["txt", "markdown", "pdf_text"],
                help="目前仅支持文本格式，PDF 需先提取文本",
            )
            doc_content = st.text_area(
                "文档内容",
                placeholder="请粘贴完整的文档内容...\n\n"
                            "提示：内容会被自动切分为文本块（chunk_size=500, overlap=50）",
                height=250,
            )

            # form_submit_button：只有点击此按钮才提交表单
            submitted = st.form_submit_button(
                "✅ 提交文档",
                use_container_width=True,
                type="primary",
            )

            if submitted:
                if not doc_title.strip():
                    st.session_state.notification = ("⚠️ 请输入文档标题", "warning")
                elif not doc_content.strip():
                    st.session_state.notification = ("⚠️ 请输入文档内容", "warning")
                else:
                    # 调用 FastAPI 后端创建文档
                    result = api_post("/documents/", {
                        "title": doc_title.strip(),
                        "content": doc_content.strip(),
                        "file_type": doc_type,
                    })
                    if result:
                        st.session_state.notification = (
                            f"✅ 文档「{doc_title}」已创建，共切分为 {result['chunk_count']} 个文本块",
                            "success"
                        )
                        st.rerun()  # 重新运行以刷新右侧文档列表

    with col_right:
        st.subheader("📋 文档列表")

        # 每 5 秒自动刷新列表（通过数据变化触发重新运行）
        # 注意：Streamlit 没有内置定时刷新，这里用刷新按钮手动控制
        if st.button("🔄 刷新列表", use_container_width=True):
            st.rerun()

        docs = api_get("/documents/", params={"limit": 50})

        if docs is None:
            st.warning("请先确认后端已启动，然后点击「检测连接」")
        elif len(docs) == 0:
            st.info("暂无文档，请上传第一篇文档")
        else:
            st.caption(f"共 {len(docs)} 篇文档")
            for doc in docs:
                # 每篇文档显示为一个可展开的卡片
                with st.expander(
                    f"📝 {doc['title']} "
                    f"（{doc['file_type']} · {doc['chunk_count']} 个块）"
                ):
                    # 创建时间
                    created = doc['created_at'][:19] if doc.get('created_at') else "未知"
                    st.caption(f"ID: {doc['id']} | 创建: {created}")

                    # 内容预览（截取前 200 字符）
                    content_preview = doc['content'][:200]
                    if len(doc['content']) > 200:
                        content_preview += "..."
                    st.text(content_preview)

                    # 操作按钮行
                    btn_col1, btn_col2, _ = st.columns([1, 1, 3])
                    with btn_col1:
                        if st.button("🗑️ 删除", key=f"del_{doc['id']}"):
                            result = api_delete(f"/documents/{doc['id']}")
                            if result:
                                st.session_state.notification = (
                                    f"🗑️ {result.get('message', '已删除')}", "success"
                                )
                                st.rerun()
                    with btn_col2:
                        if st.button("🔍 查看详情", key=f"view_{doc['id']}"):
                            # 切换到文档详情页并指定查看哪个文档
                            st.session_state.current_page = "🔍 文档详情"
                            st.session_state.view_doc_id = doc['id']
                            st.rerun()

# ============================================================
# 页面 2：🔍 文档详情
# ============================================================
elif st.session_state.current_page == "🔍 文档详情":
    st.title("🔍 文档详情")
    st.caption("查看文档内容和它的文本块切分结果")

    # 从 session_state 获取要查看的文档 ID
    target_doc_id = st.session_state.get("view_doc_id", None)

    # 文档选择器
    doc_id_input = st.number_input(
        "输入文档 ID",
        min_value=1,
        value=target_doc_id if target_doc_id else 1,
        step=1,
        key="doc_detail_id_input",
    )

    if st.button("🔍 查询", use_container_width=True, type="primary"):
        # 查询文档信息
        doc = api_get(f"/documents/{doc_id_input}")
        if doc:
            st.markdown(f"## {doc['title']}")
            st.caption(
                f"类型: {doc['file_type']} | "
                f"文本块数量: {doc['chunk_count']} | "
                f"创建: {doc['created_at'][:19]}"
            )
            st.divider()
            st.markdown(doc['content'])

        # 查询该文档的文本块
        chunks = api_get(f"/documents/{doc_id_input}/chunks", params={"limit": 50})
        if chunks:
            st.divider()
            st.subheader(f"📦 文本块列表（共 {len(chunks)} 个）")
            for chunk in chunks:
                with st.expander(
                    f"块 #{chunk['chunk_index']} "
                    f"（{len(chunk['chunk_text'])} 字符）"
                ):
                    st.text(chunk['chunk_text'])

    # 返回按钮
    if st.button("← 返回文档列表"):
        st.session_state.current_page = "📄 文档管理"
        st.rerun()

# ============================================================
# 页面 3：💬 智能问答（Week 3 的接口预留）
# ============================================================
elif st.session_state.current_page == "💬 智能问答":
    st.title("💬 智能问答")
    st.caption("基于文档内容回答问题（当前为 Mock 版本，Week 3 接入 LLM）")

    # 会话管理
    if "active_conversation_id" not in st.session_state:
        st.session_state.active_conversation_id = None

    # ---- 左侧：问答区域  |  右侧：会话历史 ----
    col_chat, col_history = st.columns([3, 2])

    with col_chat:
        # 创建新会话
        if st.session_state.active_conversation_id is None:
            if st.button("➕ 开始新会话", use_container_width=True):
                result = api_post("/conversations/", {
                    "title": f"问答 {datetime.datetime.now().strftime('%m-%d %H:%M')}"
                })
                if result:
                    st.session_state.active_conversation_id = result['id']
                    st.session_state.notification = ("✅ 新会话已创建", "success")
                    st.rerun()

        # 显示当前会话的消息
        if st.session_state.active_conversation_id:
            conv_id = st.session_state.active_conversation_id
            messages = api_get(f"/conversations/{conv_id}/messages/")
            if messages:
                for msg in messages:
                    with st.chat_message(msg['role']):
                        st.write(msg['content'])

            # 输入新问题
            user_input = st.chat_input("请输入你的问题...")
            if user_input:
                # 保存用户消息
                api_post(f"/conversations/{conv_id}/messages/", {
                    "role": "user",
                    "content": user_input,
                })

                # Mock 回答：后续 Week 3 改为 LLM 调用
                # 此处模拟检索相关文档块的逻辑
                mock_answer = (
                    f"🤖 收到你的问题：「{user_input}」\n\n"
                    f"当前为 Mock 模式。Week 3 将接入 LLM API，"
                    f"并在此基础上增加：\n"
                    f"1. 将问题转为检索向量\n"
                    f"2. 从文本块中召回 top_k 相关内容\n"
                    f"3. 将相关块 + 问题一起发给大模型\n"
                    f"4. 返回带引用的答案"
                )
                api_post(f"/conversations/{conv_id}/messages/", {
                    "role": "assistant",
                    "content": mock_answer,
                })
                st.rerun()

    with col_history:
        st.subheader("📝 会话列表")
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

        convs = api_get("/conversations/")
        if convs:
            for conv in convs:
                is_active = conv['id'] == st.session_state.active_conversation_id
                label = f"{'🟢 ' if is_active else ''}{conv['title']}（{conv['message_count']} 条）"
                if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                    st.session_state.active_conversation_id = conv['id']
                    st.rerun()

# ============================================================
# 页面 4：📊 数据库概览
# ============================================================
elif st.session_state.current_page == "📊 数据库概览":
    st.title("📊 数据库概览")
    st.caption("查看各表记录数和数据详情")

    # 统计数据卡片
    stats = api_get("/stats/")
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 文档", stats['document_count'])
        with col2:
            st.metric("📦 文本块", stats['chunk_count'])
        with col3:
            st.metric("💬 会话", stats['conversation_count'])
        with col4:
            st.metric("✉️ 消息", stats['message_count'])

    # 表详情切换
    st.divider()
    tab_choice = st.radio(
        "查看表数据",
        options=["documents", "chunks", "conversations", "messages"],
        horizontal=True,
    )

    if st.button("🔍 查询数据", use_container_width=True):
        if tab_choice == "documents":
            data = api_get("/documents/", params={"limit": 20})
            if data:
                st.subheader("📄 documents 表")
                st.dataframe(
                    [{
                        "ID": d['id'],
                        "标题": d['title'],
                        "类型": d['file_type'],
                        "块数": d['chunk_count'],
                        "内容预览": d['content'][:80] + "...",
                    } for d in data],
                    use_container_width=True,
                )
        elif tab_choice == "conversations":
            data = api_get("/conversations/")
            if data:
                st.subheader("💬 conversations 表")
                st.dataframe(
                    [{
                        "ID": c['id'],
                        "标题": c['title'],
                        "消息数": c['message_count'],
                    } for c in data],
                    use_container_width=True,
                )
        elif tab_choice == "chunks":
            st.info("chunks 数据请通过「文档详情」页面查看指定文档的文本块")
        elif tab_choice == "messages":
            st.info("messages 数据请通过「智能问答」页面查看指定会话的消息")

    # 数据库文件路径
    st.divider()
    st.caption("数据库文件位置：")
    st.code("D:\\work\\study\\FastAPI\\week2_rag.db", language="text")


# ============================================================
# 页脚
# ============================================================
st.divider()
st.caption(
    "Week 2 实践项目 | "
    "FastAPI + SQLModel + Streamlit | "
    f"API: {API_BASE_URL}/docs"
)
