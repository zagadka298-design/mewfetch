#!/usr/bin/env bash
# ~/mewfetch/install.sh
# Скрипт установки / обновления mewfetch в систему

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/mewfetch/__init__.py"
TARGET="/usr/local/bin/mewfetch"
USER_TARGET="$HOME/.local/bin/mewfetch"

echo "🐱 Установка mewfetch..."

if [ ! -f "$SOURCE" ]; then
    echo "❌ Ошибка: исходный файл не найден: $SOURCE" >&2
    exit 1
fi

# 1. Копирование в /usr/local/bin/mewfetch
echo "➡️  Копирование в $TARGET..."
if [ -w "/usr/local/bin" ] || [ -w "$TARGET" ]; then
    cp "$SOURCE" "$TARGET"
    chmod +x "$TARGET"
else
    echo "🔑 Запрос прав суперпользователя для записи в /usr/local/bin:"
    sudo cp "$SOURCE" "$TARGET"
    sudo chmod +x "$TARGET"
fi

# 2. Дублирование в ~/.local/bin/mewfetch (для локального пользователя)
mkdir -p "$HOME/.local/bin"
cp "$SOURCE" "$USER_TARGET"
chmod +x "$USER_TARGET"

# 3. Сброс кэша путей команд в shell
hash -r 2>/dev/null || true

echo "✅ mewfetch успешно установлен!"
echo "📍 Путь: $TARGET"
echo "📌 Проверка версии:"
"$TARGET" --version
