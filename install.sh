#!/usr/bin/env bash
# NAL Metadata Toolkit — installer
# Sets up a shell alias and optionally a GNOME desktop launcher.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NALMD="$SCRIPT_DIR/nalmd.py"

# Make sure nalmd.py is executable
chmod +x "$NALMD"

echo ""
echo "NAL Metadata Toolkit — Setup"
echo "=============================="
echo ""

# ── Shell alias ───────────────────────────────────────────────────────────────

ALIAS_LINE="alias nalmd='python3 $NALMD'"
SHELL_RC=""

if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [[ -n "$SHELL_RC" ]]; then
    if grep -q "alias nalmd=" "$SHELL_RC" 2>/dev/null; then
        echo "✓ Shell alias already set in $SHELL_RC"
    else
        echo "$ALIAS_LINE" >> "$SHELL_RC"
        echo "✓ Added 'nalmd' alias to $SHELL_RC"
        echo "  Run:  source $SHELL_RC  — or open a new terminal to use it."
    fi
else
    echo "  Could not detect shell config. Add this line manually to your shell profile:"
    echo "  $ALIAS_LINE"
fi

echo ""

# ── GNOME desktop launcher ────────────────────────────────────────────────────

DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_DEST="$DESKTOP_DIR/nalmd.desktop"

if command -v update-desktop-database &>/dev/null; then
    mkdir -p "$DESKTOP_DIR"
    sed "s|NALMD_PATH|$NALMD|g" "$SCRIPT_DIR/nalmd.desktop" > "$DESKTOP_DEST"
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    echo "✓ GNOME launcher installed — search for 'NAL Metadata' in Activities."
else
    echo "  GNOME not detected — skipping desktop launcher."
fi

echo ""
echo "Done. You can now run the tool by typing:  nalmd"
echo "(After sourcing your shell config or opening a new terminal.)"
echo ""
