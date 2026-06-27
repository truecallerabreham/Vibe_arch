from fastapi import FastAPI
from backend.app.api.routes import router

app = FastAPI(title="Vibe Arch API", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
