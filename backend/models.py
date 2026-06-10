"""Model management endpoints using SQLite persistence.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from .hardware import probe
from . import db

router = APIRouter()

# Initialize DB
try:
    db.init_db()
except Exception:
    # In case DB cannot be initialized in certain environments, continue with in-memory fallback
    _in_memory_models = []

class ModelInstallRequest(BaseModel):
    name: str
    source: str = 'auto'  # e.g., ollama, huggingface, local path


@router.get('/models/list')
async def list_models():
    try:
        return {'models': db.list_models()}
    except Exception:
        # fallback
        return {'models': _in_memory_models}


@router.get('/models/recommend')
async def recommend_models():
    hw = probe()
    return {'recommendations': hw.get('recommendation_hints', [])}


@router.post('/models/install')
async def install_model(req: ModelInstallRequest):
    # Persist model entry
    try:
        entry = db.add_model(req.name, req.source, status='queued')
    except Exception:
        # fallback
        entry = {'name': req.name, 'source': req.source, 'status': 'queued'}
        _in_memory_models.append(entry)
    return {'status': 'queued', 'model': entry}


@router.post('/models/remove')
async def remove_model(name: str):
    try:
        ok = db.remove_model(name)
        if not ok:
            raise HTTPException(status_code=404, detail='model not found')
        return {'status': 'removed', 'name': name}
    except Exception:
        # fallback
        global _in_memory_models
        before = len(_in_memory_models)
        _in_memory_models = [m for m in _in_memory_models if m.get('name') != name]
        if len(_in_memory_models) == before:
            raise HTTPException(status_code=404, detail='model not found')
        return {'status': 'removed', 'name': name}


@router.get('/hardware/probe')
async def hardware_probe():
    return probe()
