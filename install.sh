#!/bin/bash
echo "OriginClaw Monitor - Installer"
PYTHON=python3
command -v python3 &>/dev/null || PYTHON=python
echo "Using: $($PYTHON --version)"
$PYTHON -m pip install originclaw-monitor -q --user --break-system-packages 2>/dev/null || $PYTHON -m pip install originclaw-monitor -q --user 2>/dev/null || $PYTHON -m pip install originclaw-monitor -q 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"
echo export PATH=""$HOME/.local/bin:\$PATH"" >> $HOME/.bashrc 2>/dev/null || true
echo export PATH=""$HOME/.local/bin:\$PATH"" >> $HOME/.zshenv 2>/dev/null || true
if command -v originclaw-monitor &>/dev/null; then echo "Done! Run: originclaw-monitor init"
else echo "Done! Run: source ~/.bashrc && originclaw-monitor init"; fi
