import hashlib
import locale
import os
import platform
import subprocess
import sys
import time
import psutil
from typing import Dict, Any


def get_git_info() -> Dict[str, str]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        short_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
        
        dirty_output = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8").strip()
        is_dirty = len(dirty_output) > 0
        
        return {
            "commit": commit,
            "short_commit": short_commit,
            "is_dirty": is_dirty
        }
    except Exception:
        return {
            "commit": "unknown",
            "short_commit": "unknown",
            "is_dirty": False
        }


def get_cpu_model() -> str:
    """Attempts to get human-readable CPU model string."""
    try:
        if platform.system() == "Windows":
            return platform.processor()
        elif platform.system() == "Darwin":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode("utf-8").strip()
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def get_vectorizer_versions() -> Dict[str, str]:
    versions = {}
    
    # VTracer (Python Module)
    try:
        import vtracer
        versions["vtracer"] = vtracer.__version__ if hasattr(vtracer, '__version__') else "installed_unknown_version"
    except ImportError:
        versions["vtracer"] = "not_installed"
        
    # Potrace
    try:
        res = subprocess.run(["potrace", "--version"], capture_output=True, text=True, check=True)
        versions["potrace"] = res.stdout.strip().split('\n')[0]
    except Exception:
        versions["potrace"] = "not_installed"
        
    # Inkscape
    try:
        res = subprocess.run(["inkscape", "--version"], capture_output=True, text=True, check=True)
        versions["inkscape"] = res.stdout.strip().split('\n')[0]
    except Exception:
        versions["inkscape"] = "not_installed"
        
    return versions


def capture_environment() -> Dict[str, Any]:
    """
    Captures a comprehensive snapshot of the execution environment for reproducibility.
    Strictly avoids saving secrets.
    """
    
    # 1. OS & Hardware
    env_info = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "kernel": platform.machine(),
            "architecture": platform.architecture()[0]
        },
        "hardware": {
            "cpu_model": get_cpu_model(),
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "total_memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2)
        }
    }
    
    # 2. Python & Dependencies
    try:
        pip_freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode("utf-8").splitlines()
    except Exception:
        pip_freeze = []
        
    env_info["python"] = {
        "version": sys.version,
        "executable": sys.executable,
        "pip_freeze": pip_freeze
    }
    
    # 3. Vectorizer Executables
    env_info["vectorizer_executables"] = get_vectorizer_versions()
    
    # 4. Git Info
    env_info["git"] = get_git_info()
    
    # 5. Localization
    try:
        loc = locale.getdefaultlocale()
    except Exception:
        loc = (None, None)
        
    env_info["localization"] = {
        "locale": loc[0] if loc[0] else "unknown",
        "encoding": loc[1] if loc[1] else "unknown",
        "timezone": time.tzname
    }
    
    # 6. Safe Environment Variables
    safe_env_keys = {"PATH", "PYTHONPATH", "LANG", "LC_ALL", "TMPDIR", "USER", "SHELL"}
    unsafe_substrings = {"KEY", "TOKEN", "PASS", "SECRET", "AUTH", "CRED"}
    
    safe_env = {}
    for k, v in os.environ.items():
        # Include if in explicit safe list
        if k in safe_env_keys:
            safe_env[k] = v
            continue
            
        # Optional: Include strictly generic non-secret vars if useful, but best practice 
        # is to stick to whitelist. We will stick to the explicit whitelist and some generic flags.
        if k.startswith("XDG_") or k.startswith("LC_"):
            safe_env[k] = v
            
    env_info["environment_variables"] = safe_env
    
    return env_info

def generate_config_hash(config_path: str) -> str:
    """Generates a short hash of the config file contents."""
    if not os.path.exists(config_path):
        return "nohash"
    with open(config_path, 'rb') as f:
        content = f.read()
    return hashlib.sha1(content).hexdigest()[:7]
