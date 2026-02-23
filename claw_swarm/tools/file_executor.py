import os
import subprocess

def safe_write_file(path: str, content: str) -> str:
    """Write to file (scoped to /tmp/clawswarm-projects only)."""
    base = "/tmp/clawswarm-projects"
    os.makedirs(base, exist_ok=True)
    
    full_path = os.path.normpath(os.path.join(base, path))
    
    # Security: prevent directory traversal
    if not full_path.startswith(base):
        return "ERROR: Path outside allowed directory"
    
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)
    return f"✅ Wrote {full_path}"

def safe_run_command(command: str) -> str:
    """Run bash command (scoped, whitelisted commands only)."""
    safe_commands = ["git", "npm", "node", "vercel", "gh"]
    cmd_name = command.split()[0]
    
    if cmd_name not in safe_commands:
        return f"ERROR: {cmd_name} not allowed"
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd="/tmp/clawswarm-projects",
            timeout=300
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"ERROR: {e}"
