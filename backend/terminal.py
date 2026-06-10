"""Controlled terminal execution endpoints.
Provides a safe dry-run mode and basic dangerous-command detection.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import shlex
import subprocess
import re
from typing import Dict

router = APIRouter()

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"rm\s+-r",
    r"del\s+\/s\s+\/q",
    r"format\s+",
    r"mkfs",
    r":\\windows\\system32",
    r"shutdown\b",
    r"reboot\b",
    r"dd\s+if=",
    r"reg\s+add",
    r"reg\s+delete",
    r"Remove-Item",
    r"Start-Process",
    r"Invoke-WebRequest",
    r"powershell\b",
]


class ExecRequest(BaseModel):
    command: str
    dry_run: bool = True


def is_dangerous(cmd: str) -> Dict[str, str]:
    lowered = cmd
    for p in DANGEROUS_PATTERNS:
        if re.search(p, lowered, re.IGNORECASE):
            return {'danger': True, 'pattern': p}
    return {'danger': False}


@router.post('/terminal/exec')
async def exec_command(req: ExecRequest):
    # Check for dangerous patterns
    danger = is_dangerous(req.command)
    if danger.get('danger'):
        return {'allowed': False, 'reason': f"Matches dangerous pattern: {danger.get('pattern')}"}

    if req.dry_run:
        return {'allowed': True, 'dry_run': True, 'command': req.command}

    # Execution (synchronous, careful)
    try:
        parts = shlex.split(req.command, posix=True)
    except Exception:
        parts = req.command.split()

    try:
        # Limit execution time and output size in production
        completed = subprocess.run(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False, check=False)
        return {
            'allowed': True,
            'stdout': completed.stdout.decode(errors='replace'),
            'stderr': completed.stderr.decode(errors='replace'),
            'returncode': completed.returncode
        }
    except subprocess.TimeoutExpired:
        return {'allowed': True, 'error': 'timeout'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
