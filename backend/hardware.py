"""Hardware detection utilities for TENISN.
Returns CPU, RAM, disk, and GPU information usable by the model recommender.
"""
import platform
import psutil
import shutil
import subprocess
from typing import Dict, Any

try:
    import GPUtil
except Exception:
    GPUtil = None


def _disk_usage_best() -> Dict[str, Any]:
    try:
        parts = psutil.disk_partitions(all=False)
        if parts:
            # Pick the first mounted partition
            mount = parts[0].mountpoint
        else:
            mount = '/'
        du = psutil.disk_usage(mount)
        return {"mount": mount, "total": du.total, "free": du.free}
    except Exception:
        du = psutil.disk_usage('/')
        return {"mount": '/', "total": du.total, "free": du.free}


def probe() -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    info['platform'] = platform.system()
    info['platform_release'] = platform.release()
    try:
        info['cpu_logical_cores'] = psutil.cpu_count(logical=True)
        info['cpu_physical_cores'] = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq()
        info['cpu_freq_mhz'] = freq._asdict() if freq else None
    except Exception as e:
        info['cpu_error'] = str(e)

    try:
        vm = psutil.virtual_memory()
        info['total_ram_bytes'] = vm.total
        info['available_ram_bytes'] = vm.available
    except Exception as e:
        info['mem_error'] = str(e)

    try:
        info['disk'] = _disk_usage_best()
    except Exception as e:
        info['disk_error'] = str(e)

    # GPU detection
    gpus = []
    try:
        if GPUtil is not None:
            for g in GPUtil.getGPUs():
                gpus.append({
                    'id': g.id,
                    'name': g.name,
                    'memoryTotalMB': g.memoryTotal,
                    'memoryFreeMB': g.memoryFree,
                    'memoryUsedMB': g.memoryUsed,
                    'driver': getattr(g, 'driver', None)
                })
        else:
            gpus = None
    except Exception as e:
        info['gpus_error'] = str(e)
        gpus = None

    info['gpus'] = gpus

    # Detect nvidia-smi (CUDA) and rocm-smi (ROCm)
    info['nvidia_smi'] = bool(shutil.which('nvidia-smi'))
    info['rocm_smi'] = bool(shutil.which('rocm-smi'))

    # Simple recommendation hints
    rec = []
    try:
        if gpus and len(gpus) > 0:
            # pick largest GPU by memory
            best = max(gpus, key=lambda x: x.get('memoryTotalMB', 0) or 0)
            vram = best.get('memoryTotalMB') or 0
            if vram >= 24576:
                rec.append({'model_family': 'Gemma / Mistral / Qwen', 'reason': 'High VRAM GPU >= 24GB'})
            elif vram >= 12288:
                rec.append({'model_family': 'Qwen / CodeLlama (large)', 'reason': 'GPU >= 12GB VRAM'})
            elif vram >= 6144:
                rec.append({'model_family': 'Llama / CodeLlama (medium) - quantized works well', 'reason': 'GPU >= 6GB VRAM'})
            else:
                rec.append({'model_family': 'llama.cpp / GGUF quantized CPU models', 'reason': 'Low GPU VRAM; prefer CPU-optimized quantized models'})
        else:
            # No GPU detected
            total_ram_gb = (info.get('total_ram_bytes') or 0) // (1024**3)
            if total_ram_gb >= 32:
                rec.append({'model_family': 'llama.cpp, quantized GGUF', 'reason': 'High RAM on CPU; can run medium models quantized'})
            else:
                rec.append({'model_family': 'Tiny/Small CPU quantized models (ggml, GGUF)', 'reason': 'Limited RAM; use small CPU models'})
    except Exception:
        rec.append({'model_family': 'unknown', 'reason': 'unable to compute recommendation'})

    info['recommendation_hints'] = rec
    return info


if __name__ == '__main__':
    import json
    print(json.dumps(probe(), indent=2))
