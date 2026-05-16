# AI 转行应用开发 — 学习仓库

从嵌入式开发转行 AI 应用开发，12 周系统学习计划。目标岗位：**AI 应用开发 / RAG / Agent 工程师**。

> 当前进度：**Week 2 完成** | 下一步：Week 3 — LLM API、Prompt、结构化输出

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python) |
| 数据库 | SQLite → PostgreSQL |
| ORM | SQLAlchemy 2.0 / SQLModel |
| 前端 | Streamlit |
| 向量库 | Chroma / Qdrant |
| 大模型 | DeepSeek / 通义千问 (OpenAI 兼容接口) |
| Agent | LangGraph |
| 部署 | Docker / Docker Compose |

---

## 项目结构

```
FastAPI/
├── Readme.md                          ← 本文件
├── .gitignore
├── AI转行应用开发学习计划_周计划与资源版.docx   ← 完整 12 周学习计划
│
├── Week 1 — FastAPI 基础
│   ├── test1.py                       # FastAPI 完整入门：路由、参数、Pydantic、文档
│   ├── main.py                        # 补充练习：AfterValidator、依赖注入
│   └── week1_fastapi_quiz.html        # 第一阶段自测（12 题）
│
├── Week 2 — 数据库 + Streamlit 界面
│   ├── week2_crud.py                  # 原生 SQLite3 CRUD 入门
│   ├── week2_sql.py                   # SQLAlchemy 2.0 完整教程（10 章）
│   ├── week2_streamlit.py             # Streamlit session_state 实践（计数器）
│   ├── week2_config.py                # 集中配置：数据库、API、切分参数
│   ├── week2_models.py                # RAG 四表模型：Document/Chunk/Conversation/Message
│   ├── week2_doc_api.py               # FastAPI 后端：文档管理 API（12 个接口）
│   ├── week2_streamlit_app.py         # Streamlit 前端：四页完整界面
│   ├── week2_knowledge_summary.md     # 第二周全部知识点总结（12 章）
│   ├── week2_database_notes.pdf       # 数据库学习笔记
│   └── test2.py                       # FastAPI + SQLModel Heroes CRUD 示例
│
└── Week 3（待开始）— LLM API / Prompt / 结构化输出
```

---

## 已完成的验收标准

### Week 1 — FastAPI 基础

- [x] 本地启动 FastAPI，使用 `/docs` 查看和测试接口
- [x] 掌握 GET/POST、路径参数、查询参数、请求体
- [x] 使用 Pydantic BaseModel 定义和校验数据
- [x] 使用 Git 完成 add → commit → push 流程
- [x] 通过第一阶段 12 题自测
- [x] 能解释 FastAPI、Pydantic、OpenAPI 各自的职责

### Week 2 — 数据库 + Streamlit

- [x] 使用 SQLModel 设计 RAG 核心表（documents / chunks / conversations / messages）
- [x] FastAPI 实现完整文档 CRUD（含自动文本切分）
- [x] Streamlit 前端调用 FastAPI 后端（前后端分离）
- [x] 掌握 session_state、表单回调、侧边栏导航
- [x] 能解释为什么 RAG 需要 documents 和 chunks 分开存储
- [x] 本周 6+ 次 Git 提交，README 持续更新

---

## 快速启动

```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# Week 1：FastAPI 入门
fastapi dev test1.py
# 访问 http://127.0.0.1:8000/docs

# Week 2：文档管理系统（需要同时启动两个服务）
# 终端 1 — 后端
fastapi dev week2_doc_api.py
# 终端 2 — 前端
streamlit run week2_streamlit_app.py
```

---

## 学习资源

- [FastAPI 官方教程](https://fastapi.tiangolo.com/tutorial/)
- [Streamlit 官方文档](https://docs.streamlit.io/)
- [SQLAlchemy 2.0 教程](https://docs.sqlalchemy.org/20/tutorial/index.html)
- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [LangChain 文档](https://docs.langchain.com/oss/python/langchain/retrieval)
- [LangGraph 文档](https://docs.langchain.com/oss/python/langgraph/overview)

---

## Git 提交规范

每周至少 5 次提交，使用中文说明：

```
git status          # 查看修改状态
git add <文件>       # 暂存要提交的文件
git commit -m "说明"  # 本地提交
git push            # 推送到 GitHub
```

---

> 开始日期：2026-04 | 预计完成：12 周 | 下一里程碑：Week 3 — LLM API 接入
