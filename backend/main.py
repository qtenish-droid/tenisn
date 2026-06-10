"""
Simple FastAPI backend skeleton for TENISN.
Run with: python -m backend.main
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/models/list")
async def list_models():
    # Placeholder: return installed local models
    return {"models": []}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8001, log_level="info")
