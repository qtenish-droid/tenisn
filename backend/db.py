"""Simple SQLite persistence layer for TENISN backend.
Provides functions to initialize DB and manage installed models metadata.
"""
import os
import sqlite3
from typing import List, Dict, Any
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'tenisn.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            source TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_model(name: str, source: str, status: str = 'queued') -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat() + 'Z'
    try:
        cur.execute('INSERT INTO models (name, source, status, created_at) VALUES (?, ?, ?, ?)', (name, source, status, now))
        conn.commit()
        model_id = cur.lastrowid
        return {'id': model_id, 'name': name, 'source': source, 'status': status, 'created_at': now}
    except sqlite3.IntegrityError:
        # already exists
        cur.execute('SELECT * FROM models WHERE name = ?', (name,))
        row = cur.fetchone()
        return dict(row) if row else {'error': 'exists'}
    finally:
        conn.close()

def list_models() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM models ORDER BY id DESC')
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def remove_model(name: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM models WHERE name = ?', (name,))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0
