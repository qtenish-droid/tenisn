"""Playwright-based browser automation placeholders for TENISN.
Endpoints are safe fallbacks when Playwright is not installed. Sessions are kept in-memory for the running process.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
import uuid
import base64

router = APIRouter()

SESSIONS: Dict[str, Any] = {}
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), 'browser_sessions')
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR, exist_ok=True)


class StartReq(BaseModel):
    headless: bool = True


class NavReq(BaseModel):
    session_id: str
    url: str


class ScreenshotReq(BaseModel):
    session_id: str
    url: str
    path: str = ''


@router.post('/browser/start')
async def start_browser(req: StartReq):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return {'ok': False, 'error': 'playwright-not-installed', 'message': str(e)}

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=req.headless)
    context = browser.new_context()
    page = context.new_page()

    sid = str(uuid.uuid4())
    session_path = os.path.join(SESSIONS_DIR, sid)
    os.makedirs(session_path, exist_ok=True)
    SESSIONS[sid] = {'pw': pw, 'browser': browser, 'context': context, 'page': page, 'path': session_path}

    return {'ok': True, 'session_id': sid}


@router.post('/browser/navigate')
async def navigate(req: NavReq):
    s = SESSIONS.get(req.session_id)
    if not s:
        raise HTTPException(status_code=404, detail='session not found')
    try:
        page = s['page']
        page.goto(req.url, wait_until='load', timeout=15000)
        return {'ok': True, 'url': req.url, 'status': 'loaded'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.post('/browser/screenshot')
async def screenshot(req: ScreenshotReq):
    s = SESSIONS.get(req.session_id)
    if not s:
        raise HTTPException(status_code=404, detail='session not found')
    try:
        page = s['page']
        if req.url:
            page.goto(req.url, wait_until='load', timeout=15000)
        out_path = req.path or os.path.join(s['path'], 'screenshot.png')
        page.screenshot(path=out_path, full_page=True)
        with open(out_path, 'rb') as f:
            b = f.read()
        data_b64 = base64.b64encode(b).decode()
        return {'ok': True, 'path': out_path, 'data_b64': data_b64}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.post('/browser/close')
async def close_browser(session_id: str):
    s = SESSIONS.pop(session_id, None)
    if not s:
        raise HTTPException(status_code=404, detail='session not found')
    try:
        s['context'].close()
        s['browser'].close()
        s['pw'].stop()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
