#!/bin/bash
echo
echo '  OriginClaw Monitor — Installer'
echo '--------------------------------------'

# Find Python
PYTHON=''
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    PYTHON="$cmd"
    echo "  Python: $($PYTHON --version 2>&1)"
    break
  fi
done
if [ -z "$PYTHON" ]; then echo Python not found. Install from python.org; exit 1; fi

# Install
echo '  Installing originclaw-monitor...'
"$PYTHON" -m pip install originclaw-monitor --user -q 2>/dev/null || "$PYTHON" -m pip install originclaw-monitor --user -q --break-system-packages 2>/dev/null || true

# Fix PATH — find the actual install location
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
POSSIBLE_BINS=(
  "$HOME/Library/Python/$PY_VER/bin"
  "$HOME/.local/bin"
  "/opt/homebrew/opt/python@3.14/libexec/bin"
  "/usr/local/bin"
)

BIN_DIR=''
for d in "${POSSIBLE_BINS[@]}"; do
  if [ -f "$d/originclaw-monitor" ]; then
    BIN_DIR="$d"
    break
  fi
done

if [ -n "$BIN_DIR" ]; then
  export PATH="$BIN_DIR:$PATH"
  for RC in "$HOME/.zshrc" "$HOME/.zshenv" "$HOME/.bashrc" "$HOME/.bash_profile"; do
    if [ -f "$RC" ] || [ "$RC" = "$HOME/.zshenv" ]; then
      grep -qF "$BIN_DIR" "$RC" 2>/dev/null || echo "export PATH="$BIN_DIR:\$PATH"" >> "$RC"
    fi
  done
  echo "  Installed at: $BIN_DIR"
fi

echo
if command -v originclaw-monitor &>/dev/null; then
  echo '  Done!'
  echo '--------------------------------------'
  originclaw-monitor
else
  echo '  Installed. Open a new terminal and run:'
  echo '  originclaw-monitor'
fi
echo
