"""
FastAPI backend entry for TENISN — now with hardware probe, model endpoints, terminal, and browser automation placeholders.
Run: python -m backend.main
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title='TENISN Local Backend')

# Allow Electron (running locally) to call this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost', 'http://127.0.0.1'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Import routers (kept local to avoid import cycles)
from . import models  # noqa: E402
from . import terminal  # noqa: E402
from . import browser  # noqa: E402

app.include_router(models.router, prefix='/api')
app.include_router(terminal.router, prefix='/api')
app.include_router(browser.router, prefix='/api')


@app.get('/')
async def root():
    return {'service': 'tenisn-backend', 'status': 'ok'}


if __name__ == '__main__':
    uvicorn.run('backend.main:app', host='127.0.0.1', port=8001, log_level='info')
