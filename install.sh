#!/bin/bash
set -e
echo ""
echo "  OriginClaw Monitor - Installer"
echo "--------------------------------------"

# Detect Python
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    MAJ=$("$cmd" -c "import sys; print(sys.version_info.major)")
    MIN=$("$cmd" -c "import sys; print(sys.version_info.minor)")
    if [ "$MAJ" -ge 3 ] && [ "$MIN" -ge 9 ]; then PYTHON="$cmd"; break; fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "  Python 3.9+ not found. Install from python.org"
  exit 1
fi
echo "  Python: $($PYTHON --version)"

# Install package
echo "  Installing originclaw-monitor..."
"$PYTHON" -m pip install --upgrade originclaw-monitor -q 2>/dev/null || "$PYTHON" -m pip install --upgrade originclaw-monitor -q --user 2>/dev/null || true

# Fix PATH for all platforms
LOCAL_BIN="$HOME/.local/bin"
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAC_BIN="$HOME/Library/Python/$PY_VER/bin"

for BIN_DIR in "$LOCAL_BIN" "$MAC_BIN" "/usr/local/bin" "/opt/homebrew/bin"; do
  if [ -f "$BIN_DIR/originclaw-monitor" ]; then
    export PATH="$BIN_DIR:$PATH"
    for RC in "$HOME/.zshenv" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
      if [ -f "$RC" ] || [ "$RC" = "$HOME/.zshenv" ]; then
        grep -qF "$BIN_DIR" "$RC" 2>/dev/null || echo "export PATH="$BIN_DIR:\$PATH"" >> "$RC"
      fi
    done
    echo "  Found at: $BIN_DIR"
    break
  fi
done

# Verify
if command -v originclaw-monitor &>/dev/null; then
  echo ""
  echo "  Installation complete!"
  echo "--------------------------------------"
  echo "  Run: originclaw-monitor init"
else
  echo ""
  echo "  Installed. Restart terminal then run:"
  echo "  originclaw-monitor init"
  echo ""
  echo "  Or run directly:"
  echo "  $PYTHON -m originclaw_monitor.cli init"
fi
echo ""
