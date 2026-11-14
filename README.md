<div align="center">

<h1>🐱 MewFetch</h1>

<p><em>Лёгкая утилита для отображения системной информации с ASCII-артом кота</em></p>

![screenshot](screenshot.png)

<br/>

[![AUR](https://img.shields.io/aur/version/mewfetch?color=1793d1&logo=arch-linux&label=AUR)](https://aur.archlinux.org/packages/mewfetch)
[![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey?logo=linux)](https://kernel.org/)

</div>

---

**MewFetch** — минималистичная альтернатива `neofetch` и `fastfetch`, написанная на чистом Python 3.  
Никаких внешних зависимостей. Только кот и твоя система. 🐾

---

## ✨ Возможности

- **Нулевые зависимости** — использует только стандартную библиотеку Python и `/proc`
- **ASCII-арт кота** — три стиля в одном, рядом с системной информацией
- **Поддержка Wayland и X11** — разрешение экрана через `hyprctl` (Hyprland) или `xrandr`
- **Автоопределение WM** — Hyprland, Sway, i3, bspwm, Openbox и другие
- **Цветной вывод** — ANSI-цвета, цветовая полоска в конце
- **Быстрый запуск** — читает `/proc` напрямую, не вызывает лишних процессов

---

## 📊 Выводимая информация

| Поле | Источник |
|------|----------|
| **OS** | `/etc/os-release` |
| **Kernel** | `platform.release()` |
| **Hostname** | `platform.node()` |
| **Uptime** | `/proc/uptime` |
| **CPU** | `/proc/cpuinfo` |
| **RAM** | `/proc/meminfo` |
| **Resolution** | `hyprctl monitors` / `xrandr` |
| **WM** | env-переменные / список процессов |
| **Terminal** | `$TERM_PROGRAM`, `$TERM`, `/proc` |
| **Shell** | `$SHELL` |

---

## 📦 Установка

### Из AUR (рекомендуется для Arch Linux)

```bash
# С помощью yay
yay -S mewfetch

# С помощью paru
paru -S mewfetch
```

### Вручную через makepkg

```bash
git clone https://aur.archlinux.org/mewfetch.git
cd mewfetch
makepkg -si
```

### Из исходников (любой дистрибутив)

```bash
git clone https://github.com/zagadka298-design/mewfetch.git
cd mewfetch
chmod +x mewfetch.py

# Запуск напрямую
./mewfetch.py

# Установка в систему
sudo install -Dm755 mewfetch.py /usr/local/bin/mewfetch
```

---

## 🔧 Зависимости

| Зависимость | Обязательная | Назначение |
|-------------|:---:|-----------|
| **Python 3.10+** | ✅ | Интерпретатор |
| `hyprctl` | ⬜ | Разрешение экрана на Hyprland |
| `xrandr` | ⬜ | Разрешение экрана на X11 |

> Все остальные данные считываются напрямую из `/proc` и `/etc` — никаких дополнительных пакетов не требуется.

---

## 🚀 Использование

```bash
mewfetch
```

Вот и всё. Никаких флагов, никаких конфигов — просто запусти.

---

## 🖥️ Совместимость

| Дистрибутив | Статус |
|------------|:------:|
| EndeavourOS | ✅ |
| Arch Linux | ✅ |
| Manjaro | ✅ |
| Другие Linux | ✅ (частично) |
| macOS / Windows | ❌ |

**WM/Compositor:**  
Hyprland · Sway · i3 · bspwm · Openbox · dwm · xmonad · Awesome · Fluxbox · KWin · Mutter · XFWM4

---

## 📄 Лицензия

Распространяется под лицензией [MIT](LICENSE).  
Делай что хочешь, только не убирай копирайт. 🐱

---

<div align="center">
  <sub>Сделано с ♡ и слишком большим количеством кофе</sub>
</div>
