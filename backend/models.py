"""Model management endpoints (placeholder implementations).
These endpoints will later drive model installation, removal, optimization, and querying of local runtimes.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from .hardware import probe

router = APIRouter()

# In-memory placeholder for installed models (persist to DB later)
_installed_models: List[dict] = []

class ModelInstallRequest(BaseModel):
    name: str
    source: str = 'auto'  # e.g., ollama, huggingface, local path


@router.get('/models/list')
async def list_models():
    return {'models': _installed_models}


@router.get('/models/recommend')
async def recommend_models():
    hw = probe()
    return {'recommendations': hw.get('recommendation_hints', [])}


@router.post('/models/install')
async def install_model(req: ModelInstallRequest):
    # Placeholder: Real implementation will validate, download, verify, and register model
    entry = {'name': req.name, 'source': req.source, 'status': 'queued'}
    _installed_models.append(entry)
    return {'status': 'queued', 'model': entry}


@router.post('/models/remove')
async def remove_model(name: str):
    global _installed_models
    before = len(_installed_models)
    _installed_models = [m for m in _installed_models if m.get('name') != name]
    if len(_installed_models) == before:
        raise HTTPException(status_code=404, detail='model not found')
    return {'status': 'removed', 'name': name}


@router.get('/hardware/probe')
async def hardware_probe():
    return probe()
