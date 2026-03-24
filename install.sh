#!/bin/bash
echo OriginClaw Monitor Installer
python3 -m pip install originclaw-monitor --break-system-packages --ignore-installed 2>&1 | tail -5
export PATH=/usr/local/bin:$HOME/.local/bin:$PATH
echo export PATH=/usr/local/bin:$HOME/.local/bin:$PATH >> $HOME/.bashrc
if command -v originclaw-monitor &>/dev/null; then
  echo Done. Run: originclaw-monitor init
else
  echo Installed. Run: source ~/.bashrc then originclaw-monitor init
fi
