from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


# 基础模型，定义英雄共享字段
class HeroBase(SQLModel):
    name: str = Field(index=True)  # 英雄名称，设置索引方便查询
    age: int | None = Field(default=None, index=True)  # 年龄，可选，设置索引


# 数据库表模型：继承 HeroBase 并增加 id 和 secret_name
class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)  # 主键，SQLite 会自动生成
    secret_name: str  # 英雄真实姓名，不会在公开模型中直接返回


# 对外返回的模型，不包含 secret_name
class HeroPublic(HeroBase):
    id: int


# 创建英雄时使用的请求模型
class HeroCreate(HeroBase):
    secret_name: str


# 更新英雄时使用的模型，所有字段可选
class HeroUpdate(HeroBase):
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}  # SQLite 特有，避免多线程访问冲突
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)  # 根据模型创建 SQLite 表


def get_session():
    with Session(engine) as session:
        yield session  # 每个请求使用一个数据库会话


SessionDep = Annotated[Session, Depends(get_session)]  # 依赖注入数据库 session
app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()  # 应用启动时创建数据库表结构


@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    # 创建新英雄，使用 HeroCreate 验证输入数据
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()  # 事务提交，写入数据库
    session.refresh(db_hero)  # 刷新对象，获取数据库生成的 id
    return db_hero


@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    # 查询英雄列表，支持分页查询 offset 和 limit
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    # 查询指定 id 的英雄
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDep):
    # 更新指定 id 的英雄，允许部分字段更新
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)  # 只获取真实传入的字段
    hero_db.sqlmodel_update(hero_data)  # 将新字段写入数据库模型
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db


@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    # 删除指定 id 的英雄
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}  # 删除成功返回简单 JSON