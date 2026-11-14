from fastapi import FastAPI

from app.routes import auth, capacity, inventory, queue, recommendations

app = FastAPI(title="Nest API")
app.include_router(auth.router)
app.include_router(capacity.router)
app.include_router(inventory.router)
app.include_router(queue.router)
app.include_router(recommendations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
