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
- **Параллельный сбор данных** — все поля собираются одновременно через `threading`
- **19 информационных полей** — включая GPU, диск, батарею, пакеты, IP и тему
- **6 цветовых тем** — pink, blue, green, red, cyan, mono
- **4 стиля ASCII-кота** — classic, small, sleeping, box
- **Полноценный CLI** — `--style`, `--theme`, `--fields`, `--json` и другие
- **Конфиг файл** — сохрани настройки в `~/.config/mewfetch/config`
- **Поддержка Wayland и X11** — разрешение через `hyprctl` или `xrandr`
- **JSON-вывод** — для использования в скриптах

---

## 📊 Выводимая информация

| Поле | Источник |
|------|----------|
| **OS** | `/etc/os-release` |
| **Kernel** | `platform.release()` |
| **Hostname** | `platform.node()` |
| **Uptime** | `/proc/uptime` |
| **CPU** | `/proc/cpuinfo` |
| **GPU** | `lspci -mm` |
| **RAM** | `/proc/meminfo` |
| **Swap** | `/proc/meminfo` |
| **Disk** | `os.statvfs("/")` |
| **Resolution** | `hyprctl monitors` / `xrandr` |
| **WM** | env-переменные / список процессов |
| **DE** | `XDG_CURRENT_DESKTOP` |
| **Terminal** | `$TERM_PROGRAM`, `$TERM`, `/proc` |
| **Shell** | `$SHELL` |
| **Packages** | pacman / dpkg / rpm / flatpak / snap |
| **Battery** | `/sys/class/power_supply` |
| **IP** | `socket` / `hostname -I` |
| **Theme** | `gsettings` / `gtk-3.0/settings.ini` |
| **Font** | `gsettings` / Hyprland config |

---

## 📦 Установка

### Из AUR (рекомендуется для Arch Linux)

```bash
yay -S mewfetch
# или
paru -S mewfetch
```

### Из исходников (любой дистрибутив)

```bash
git clone https://github.com/zagadka298-design/mewfetch.git
cd mewfetch
chmod +x mewfetch.py
./mewfetch.py

# Установка в систему
sudo install -Dm755 mewfetch.py /usr/local/bin/mewfetch
```

---

## 🚀 Использование

```bash
# Базовый запуск
mewfetch

# Выбрать стиль кота
mewfetch --style sleeping

# Выбрать цветовую тему
mewfetch --theme blue

# Показать только нужные поля
mewfetch --fields OS,CPU,RAM,GPU,Disk

# Без цветов (для pipe/скриптов)
mewfetch --no-color

# Без ASCII-арта
mewfetch --no-art

# Вывод в JSON
mewfetch --json

# Сохранить настройки
mewfetch --style sleeping --theme cyan --save-config

# Показать все стили
mewfetch --list-styles

# Показать все темы
mewfetch --list-themes
```

---

## ⚙️ Конфиг файл

Настройки хранятся в `~/.config/mewfetch/config`:

```ini
# mewfetch config
style   = classic
theme   = pink
show_na = false
```

Быстрое создание через CLI:
```bash
mewfetch --style sleeping --theme cyan --save-config
```

---

## 🎨 Темы и стили

### Темы (`--theme`)
| Тема | Акцент |
|------|--------|
| `pink` | Розовый (по умолчанию) |
| `blue` | Синий |
| `green` | Зелёный |
| `red` | Красный |
| `cyan` | Голубой |
| `mono` | Монохромный |

### Стили кота (`--style`)
| Стиль | Описание |
|-------|----------|
| `classic` | Три кота в одном (по умолчанию) |
| `small` | Маленький и компактный |
| `sleeping` | Дремлющий котик |
| `box` | В рамочке |

---

## 🔧 Зависимости

| Зависимость | Обязательная | Назначение |
|-------------|:---:|-----------|
| **Python 3.10+** | ✅ | Интерпретатор |
| `lspci` | ⬜ | Информация о GPU |
| `hyprctl` | ⬜ | Разрешение на Hyprland |
| `xrandr` | ⬜ | Разрешение на X11 |
| `gsettings` | ⬜ | GTK-тема и шрифт |

> Все основные данные считываются напрямую из `/proc` и `/etc` — без лишних пакетов.

---

## 🖥️ Совместимость

| Дистрибутив | Статус |
|------------|:------:|
| EndeavourOS | ✅ |
| Arch Linux | ✅ |
| Manjaro | ✅ |
| Ubuntu / Debian | ✅ |
| Fedora / openSUSE | ✅ |
| Другие Linux | ✅ |
| macOS / Windows | ❌ |

**WM/Compositor:**  
Hyprland · Sway · i3 · bspwm · Openbox · dwm · xmonad · Awesome · Fluxbox · KWin · Mutter · XFWM4 · Wayfire · River · Niri · labwc

---

## 📄 Лицензия

Распространяется под лицензией [MIT](LICENSE).  
Делай что хочешь, только не убирай копирайт. 🐱

---

<div align="center">
  <sub>Сделано с ♡ и слишком большим количеством кофе</sub>
</div>
