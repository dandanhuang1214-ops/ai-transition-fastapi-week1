# FastAPI Week 1 Practice

这是 AI 转行应用开发第一阶段的 FastAPI 练习项目。

## 当前内容

- FastAPI app
- GET 接口
- POST 接口
- 路径参数
- 查询参数
- 请求体
- Pydantic BaseModel
- 自动 API 文档

## 启动方式

```powershell
fastapi dev main.py
```

## 关于 Git 的一些基础命令

- `git status`
  - 查看当前工作区和暂存区的修改状态。
  - 用来确认哪些文件已修改、哪些文件已准备提交。
- `git add .`
  - 将所有修改过的文件添加到暂存区。
  - 相当于告诉 Git“我想把这些改动包含进下一次提交”。
- `git commit -m "说明文字"`
  - 将暂存区中的改动保存为一个本地提交。
  - `-m` 后面跟的是本次提交的说明，建议简短清晰。
- `git push`
  - 把本地分支的提交上传到远程仓库（例如 GitHub）。
  - 一般需要在本地有新提交后才能推送。

> 备注：`git push` 只会上传已经提交的内容，不能直接上传工作区中的未提交改动。也就是说，通常你需要先 `git add`，再 `git commit`，最后 `git push`。

- `git pull`
  - 从远程仓库拉取最新改动并合并到当前分支。
  - 常用于同步远程仓库与本地仓库。
- `git log`
  - 查看历史提交记录。
  - 可以帮助你确认已经提交了哪些版本。
- `git diff`
  - 查看当前修改与上一版本之间的差异。
  - 对比未提交内容时非常有用。

---

# FastAPI Week 2 Practice

这是一个基于 FastAPI 和 SQLModel 的简单 REST API。

## 当前内容

- SQLModel 模型定义（HeroBase、Hero、HeroPublic、HeroCreate、HeroUpdate）
- SQLite 数据库连接和会话管理
- POST /heroes/：创建英雄（返回 HeroPublic，不含 secret_name）
- GET /heroes/：查询英雄列表（支持分页 offset 和 limit）
- GET /heroes/{hero_id}：查询单个英雄
- PATCH /heroes/{hero_id}：部分更新英雄（只更新传入字段）
- DELETE /heroes/{hero_id}：删除英雄
- 依赖注入数据库会话（SessionDep）
- 自动 API 文档生成

## 启动方式

```powershell
fastapi dev test2.py
```

---

# Week 2 CRUD Practice

这是一个使用原生 SQLite3 模块的简单 CRUD 示例。

## 当前内容

- SQLite 数据库连接
- 创建表结构
- 插入数据
- 查询数据
- 事务提交

## 运行方式

```powershell
python week2_crud.py
```

## 输出示例

```
[(1, 'apple', 12.5)]
```
