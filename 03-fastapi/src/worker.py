from fastapi import FastAPI, Request
from pydantic import BaseModel


async def on_fetch(request, env):
    import asgi

    return await asgi.fetch(app, request, env)


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.get("/env")
async def env(req: Request):
    env = req.scope["env"]
    return {
        "message": "Here is an example of getting an environment variable: "
        + env.MESSAGE
    }


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@app.post("/items/")
async def create_item(item: Item):
    return item


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
