from fastapi import FastAPI
from routes.router import api_router

app = FastAPI(title="EDU-MIND API", version="1.0.0")
app.include_router(api_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
