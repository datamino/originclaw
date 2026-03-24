#!/bin/bash
echo OriginClaw Monitor Installer
PYTHON=python3
command -v python3 &>/dev/null || { echo Python3 not found; exit 1; }
echo Python: zsh:1: command not found: --version

# Try install methods in order
 -m pip install originclaw-monitor --break-system-packages 2>&1 | tail -3
 -m pip install originclaw-monitor --user 2>&1 | tail -3

# Find where it installed
INSTALLED=
echo Installed at: 

if [ -n "" ]; then
  export PATH=:/Users/valen/Library/Python/3.9/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin
  echo export PATH=:$PATH >> /Users/valen/.bashrc
  echo export PATH=:$PATH >> /Users/valen/.zshenv
  echo Done. Running init...
   init
else
  echo Could not find installed binary. Trying direct run:
   -m originclaw_monitor.cli init 2>&1 | head -5
fi
