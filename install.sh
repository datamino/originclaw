#!/bin/bash
set -e
echo OriginClaw Monitor Installer
PYTHON=python3
$PYTHON -m pip install --upgrade originclaw-monitor -q 2>/dev/null || true

for b in $HOME/Library/Python/3.9/bin $HOME/Library/Python/3.10/bin $HOME/Library/Python/3.11/bin $HOME/.local/bin; do
  [ -d "$b" ] && export PATH="$b:$PATH" && echo export PATH=""$b:\$PATH"" >> $HOME/.zshenv
done

echo Done! Run: originclaw-monitor init
