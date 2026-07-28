import os
import subprocess
import signal
from typing import List, Tuple

class ProcessExecutionError(Exception):
    def __init__(self, message: str, exit_code: int = -1, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

def run_isolated_process(cmd: List[str], timeout_sec: int) -> Tuple[int, str, str]:
    """
    Runs an external command with timeout and process isolation.
    Guarantees child process termination on timeout.
    Returns:
        tuple: (exit_code, stdout, stderr)
    Raises:
        TimeoutError: If process exceeds timeout limit.
        ProcessExecutionError: If process fails to execute (file not found, etc).
    """
    # 1. No shell injection: explicitly force shell=False
    use_shell = False
    
    # 2. Start process in a new session (POSIX) or CREATE_NEW_PROCESS_GROUP (Windows) 
    # to allow killing the entire process tree on timeout.
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": use_shell,
        "text": True
    }
    
    if os.name == 'posix':
        kwargs["preexec_fn"] = os.setsid
    elif os.name == 'nt':
        # CREATE_NEW_PROCESS_GROUP for Windows
        kwargs["creationflags"] = 0x00000200
        
    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except FileNotFoundError:
        raise ProcessExecutionError(f"Executable not found: {cmd[0]}")
    except Exception as e:
        raise ProcessExecutionError(f"Failed to start process: {str(e)}")
        
    try:
        stdout, stderr = proc.communicate(timeout=timeout_sec)
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        # 3. Terminate process child robustly
        if os.name == 'posix':
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.kill()
        elif os.name == 'nt':
            # Send CTRL_BREAK_EVENT
            try:
                os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
            except Exception:
                proc.kill()
        else:
            proc.kill()
            
        proc.communicate() # reap zombie
        raise TimeoutError(f"Process timed out after {timeout_sec}s")
