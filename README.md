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
- **Пользовательский логотип** — ASCII-арт или PNG/JPG через `~/.config/mewfetch/config.json`
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

### Из исходников (любой дистрибутив)

```bash
git clone https://github.com/zagadka298-design/mewfetch.git
cd mewfetch
pip install .
```

После этого команда `mewfetch` будет доступна глобально.

### Запуск без установки

```bash
git clone https://github.com/zagadka298-design/mewfetch.git
cd mewfetch
python3 -m mewfetch
```

### Из AUR (Arch Linux)

> [!WARNING]
> AUR-пакет пока не обновлён до v2.1.0 — используйте установку из исходников выше.

```bash
yay -S mewfetch
# или
paru -S mewfetch
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

Настройки хранятся в `~/.config/mewfetch/config` (создаётся автоматически при первом запуске):

```ini
# mewfetch config
style    = classic
theme    = pink
# fields = OS, CPU, RAM, GPU
show_na  = false
no_color = false
no_art   = false
```

Быстрое сохранение настроек через CLI:
```bash
mewfetch --style sleeping --theme cyan --save-config
```

---

## 🖼️ Кастомный логотип (config.json)

Помимо основного конфига, mewfetch читает `~/.config/mewfetch/config.json` для настройки логотипа/картинки слева от информации.

Файл создаётся автоматически при первом запуске:

```json
{
  "logo_path": "",
  "logo_type": "ascii"
}
```

### Параметры

| Параметр    | Тип    | Значение по умолчанию | Описание |
|-------------|--------|-----------------------|----------|
| `logo_path` | string | `""`                  | Путь к файлу логотипа. Пустая строка → стандартный кот. Поддерживаются `~` и переменные окружения. |
| `logo_type` | string | `"ascii"`             | Тип файла: `"ascii"` — текстовый арт, `"image"` — PNG/JPG. |

### Пример 1: ASCII-арт из файла

1. Создайте файл с артом, например `~/.config/mewfetch/mycat.txt`:
   ```
      /\_____/\
     /  ^   ^  \
    ( ==  v  == )
     )   mew   (
    (__(_____)__)
   ```

2. Укажите путь в `~/.config/mewfetch/config.json`:
   ```json
   {
     "logo_path": "~/.config/mewfetch/mycat.txt",
     "logo_type": "ascii"
   }
   ```

### Пример 2: PNG/JPG изображение

```json
{
  "logo_path": "~/Pictures/mylogo.png",
  "logo_type": "image"
}
```

> [!IMPORTANT]
> Для отображения изображений поддерживаются два бэкенда:
> - **Kitty Graphics Protocol** — работает автоматически в терминале [kitty](https://sw.kovidgoyal.net/kitty/)
> - **term-image** — универсальная библиотека для других терминалов (установка: `pip install term-image`)

```bash
# Установить поддержку изображений
pip install term-image
# или
pip install "mewfetch[image]"
```

> [!NOTE]
> Если файл по указанному `logo_path` не найден, mewfetch автоматически выведет стандартного кота и покажет предупреждение в stderr.

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
| `term-image` | ⬜ | Вывод PNG/JPG логотипа (`pip install term-image`) |

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
