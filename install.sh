#!/usr/bin/env bash
# ~/mewfetch/install.sh
# Installation / update script for mewfetch

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/mewfetch/__init__.py"
TARGET="/usr/local/bin/mewfetch"
USER_TARGET="$HOME/.local/bin/mewfetch"

echo "🐱 Installing mewfetch..."

if [ ! -f "$SOURCE" ]; then
    echo "❌ Error: source file not found: $SOURCE" >&2
    exit 1
fi

# 1. Copy to /usr/local/bin/mewfetch
echo "➡️  Copying to $TARGET..."
if [ -w "/usr/local/bin" ] || [ -w "$TARGET" ]; then
    cp "$SOURCE" "$TARGET"
    chmod +x "$TARGET"
else
    echo "🔑 Requesting superuser permissions to write to /usr/local/bin:"
    sudo cp "$SOURCE" "$TARGET"
    sudo chmod +x "$TARGET"
fi

# 2. Duplicate to ~/.local/bin/mewfetch (for local user)
mkdir -p "$HOME/.local/bin"
cp "$SOURCE" "$USER_TARGET"
chmod +x "$USER_TARGET"

# 3. Reset command path cache in shell
hash -r 2>/dev/null || true

echo "✅ mewfetch successfully installed!"
echo "📍 Location: $TARGET"
echo "📌 Version check:"
"$TARGET" --version
