import sys, os, subprocess

def fix_path():
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    home = os.path.expanduser("~")
    
    candidates = [
        f"{home}/Library/Python/{ver}/bin",
        f"{home}/.local/bin",
        "/opt/homebrew/opt/python@3.14/libexec/bin",
    ]
    
    bin_dir = None
    for d in candidates:
        if os.path.isfile(os.path.join(d, "originclaw-monitor")):
            bin_dir = d
            break
    
    if not bin_dir:
        return
    
    if bin_dir in os.environ.get("PATH", ""):
        return
    
    rc_files = [
        f"{home}/.zshrc",
        f"{home}/.zshenv",
        f"{home}/.bashrc",
        f"{home}/.bash_profile",
    ]
    
    line = f"export PATH="{bin_dir}:\$PATH""
    for rc in rc_files:
        if os.path.exists(rc):
            content = open(rc).read()
            if bin_dir not in content:
                with open(rc, "a") as f:
                    f.write(f"
{line}
")
    
    # Always write to .zshenv so it applies everywhere
    zshenv = f"{home}/.zshenv"
    content = open(zshenv).read() if os.path.exists(zshenv) else ""
    if bin_dir not in content:
        with open(zshenv, "a") as f:
            f.write(f"
{line}
")

if __name__ == "__main__":
    fix_path()
