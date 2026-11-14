from fastapi import FastAPI

from app.routes import analytics, auth, capacity, checkout, inventory, profile, queue, recommendations

app = FastAPI(title="Nest API")
app.include_router(analytics.router)
app.include_router(auth.router)
app.include_router(capacity.router)
app.include_router(checkout.router)
app.include_router(inventory.router)
app.include_router(profile.router)
app.include_router(queue.router)
app.include_router(recommendations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
