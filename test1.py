from enum import Enum
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel


app = FastAPI(
    title="AI Transition Week 1 API",
    description="FastAPI first-stage practice: routes, path params, query params, request body, and docs.",
    version="0.1.0",
)


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


fake_items_db = [
    {"item_id": "Foo"},
    {"item_id": "Bar"},
    {"item_id": "Baz"},
]


@app.get("/")
async def root():
    return {"message": "AI Transition API is running"}


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "ai-transition-week1-api",
        "version": "0.1.0",
    }


@app.get("/items/")
async def read_items(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return fake_items_db[skip : skip + limit]


@app.get("/items/{item_id}")
async def read_item(
    item_id: str,
    q: Annotated[str | None, Query(max_length=50)] = None,
    short: bool = False,
):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {
            "model_name": model_name,
            "message": "Deep Learning FTW!",
        }
    if model_name is ModelName.resnet:
        return {
            "model_name": model_name,
            "message": "Have some residuals.",
        }
    return {
        "model_name": model_name,
        "message": "LeCNN all the images.",
    }
