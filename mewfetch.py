#!/usr/bin/env python3
"""
mewfetch.py — аналог fastfetch для Linux (EndeavourOS)
Выводит информацию о системе с ASCII-артом кота слева
"""

import os
import platform
import subprocess
import shutil

# ──────────────────────────────────────────────
# ANSI-цвета
# ──────────────────────────────────────────────
RESET   = "\033[0m"
PINK    = "\033[1;35m"   # ярко-розовый для заголовков
WHITE   = "\033[1;37m"   # белый для значений
GRAY    = "\033[0;37m"   # серый для рамок / разделителей
CYAN    = "\033[1;36m"   # голубой — акцент (имя пользователя)

# ──────────────────────────────────────────────
# ASCII-арт кота (19 строк)
# ──────────────────────────────────────────────
CAT = [
    r"   /\_____/\   ",
    r"  /  o   o  \  ",
    r" ( ==  ^  == ) ",
    r"  )         (  ",
    r" (           ) ",
    r"( (  )   (  ) )",
    r"(__(__)___(__)__)",
    r"                ",
    r"  |\      _,,,---,,_   ",
    r"  /,`.-'`'    -.  ;-;;,_ ",
    r" |,4-  ) )-,_..;\ (  `'-' ",
    r"'---''(_/--'  `-'\_) ",
    r"                ",
    r"   /\   /\      ",
    r"  ( owo  )     ",
    r"  |  ♡  |     ",
    r"  (_____)      ",
    r"  mew mew~     ",
    r"                ",
]

# ──────────────────────────────────────────────
# Вспомогательная функция: запустить команду
# Возвращает строку вывода или None при ошибке
# ──────────────────────────────────────────────
def run(cmd: list[str], timeout: int = 3) -> str | None:
    """Запускает внешнюю команду, возвращает stdout или None."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout.strip()
        return output if output else None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return None

# ──────────────────────────────────────────────
# Сборщики данных
# ──────────────────────────────────────────────

def get_os() -> str:
    """
    Читаем /etc/os-release напрямую — самый надёжный способ
    получить «красивое» название дистрибутива.
    """
    try:
        with open("/etc/os-release") as f:
            data = {}
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, _, val = line.partition("=")
                    data[key] = val.strip('"')
        name    = data.get("PRETTY_NAME", "")
        version = data.get("VERSION", "")
        return name or platform.system()
    except OSError:
        return platform.system()


def get_kernel() -> str:
    """platform.release() == uname -r."""
    return platform.release()


def get_hostname() -> str:
    """platform.node() читает /etc/hostname."""
    return platform.node()


def get_uptime() -> str:
    """
    /proc/uptime содержит секунды с момента загрузки.
    Переводим в дни / часы / минуты.
    """
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        days    = int(seconds // 86400)
        hours   = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        parts = []
        if days:    parts.append(f"{days}д")
        if hours:   parts.append(f"{hours}ч")
        parts.append(f"{minutes}мин")
        return " ".join(parts)
    except OSError:
        return "N/A"


def get_cpu() -> str:
    """
    Парсим /proc/cpuinfo:
      model name — модель процессора
      processor  — количество логических ядер
    """
    model  = "Unknown"
    cores  = 0
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name") and model == "Unknown":
                    model = line.split(":", 1)[1].strip()
                elif line.startswith("processor"):
                    cores += 1
    except OSError:
        pass
    return f"{model} ({cores} cores)"


def get_ram() -> str:
    """
    /proc/meminfo содержит MemTotal и MemAvailable в кБ.
    Используемая = Total - Available.
    """
    try:
        data = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, _, val = line.partition(":")
                data[key.strip()] = val.strip().split()[0]   # значение в кБ
        total     = int(data.get("MemTotal",     0)) // 1024
        available = int(data.get("MemAvailable", 0)) // 1024
        used      = total - available
        return f"{used} MiB / {total} MiB"
    except OSError:
        return "N/A"


def get_resolution() -> str:
    """
    Пробуем несколько способов (в порядке приоритета):
    1. hyprctl monitors -j  (Hyprland)
    2. xrandr              (X11)
    """
    # 1. Hyprland
    out = run(["hyprctl", "monitors", "-j"])
    if out:
        import json
        try:
            monitors = json.loads(out)
            resolutions = []
            for m in monitors:
                w = m.get("width", 0)
                h = m.get("height", 0)
                r = m.get("refreshRate", 0)
                if w and h:
                    resolutions.append(f"{w}x{h}@{r:.0f}Hz")
            if resolutions:
                return ", ".join(resolutions)
        except (json.JSONDecodeError, KeyError):
            pass

    # 2. xrandr
    out = run(["xrandr"])
    if out:
        for line in out.splitlines():
            if " connected" in line and "x" in line:
                # ищем паттерн типа "1920x1080+0+0"
                for token in line.split():
                    if "x" in token and "+" in token:
                        return token.split("+")[0]

    return "N/A"


def get_wm() -> str:
    """
    1. Смотрим переменные HYPRLAND_INSTANCE_SIGNATURE и XDG_CURRENT_DESKTOP
    2. Иначе ищем процесс среди известных WM
    """
    # Hyprland
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "Hyprland"

    # XDG переменные
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    if desktop:
        return desktop

    # Поиск по запущенным процессам
    known_wms = [
        "hyprland", "sway", "i3", "openbox", "bspwm",
        "dwm", "xmonad", "awesome", "fluxbox", "kwin_wayland",
        "mutter", "marco", "xfwm4", "herbstluftwm",
    ]
    out = run(["ps", "-eo", "comm"])
    if out:
        running = set(out.lower().splitlines())
        for wm in known_wms:
            if wm in running:
                return wm.capitalize()

    return "N/A"


def get_terminal() -> str:
    """
    Порядок поиска:
    1. $TERM_PROGRAM (kitty, iTerm, etc.)
    2. $TERM            (alacritty, xterm, …)
    3. basename родительского процесса через /proc
    """
    term = os.environ.get("TERM_PROGRAM") or os.environ.get("TERM")
    if term:
        return term

    # Идём по дереву процессов
    try:
        ppid = os.getppid()
        with open(f"/proc/{ppid}/comm") as f:
            return f.read().strip()
    except OSError:
        return "N/A"


def get_shell() -> str:
    """$SHELL или /proc/<ppid>/exe."""
    shell = os.environ.get("SHELL", "")
    return os.path.basename(shell) if shell else "N/A"


# ──────────────────────────────────────────────
# Форматирование вывода
# ──────────────────────────────────────────────

def fmt_row(label: str, value: str) -> str:
    """Возвращает одну строку: «  LABEL: value»."""
    return f"  {PINK}{label:<12}{RESET}: {WHITE}{value}{RESET}"


def render():
    """Собирает все данные и рисует вывод."""
    user     = os.environ.get("USER", os.environ.get("LOGNAME", "user"))
    host     = get_hostname()

    # Таблица информации
    info_lines = [
        "",                                              # пустая строка-отступ
        f"  {CYAN}{user}{RESET}@{CYAN}{host}{RESET}",
        f"  {GRAY}{'─' * 28}{RESET}",
        fmt_row("OS",         get_os()),
        fmt_row("Kernel",     get_kernel()),
        fmt_row("Hostname",   host),
        fmt_row("Uptime",     get_uptime()),
        fmt_row("CPU",        get_cpu()),
        fmt_row("RAM",        get_ram()),
        fmt_row("Resolution", get_resolution()),
        fmt_row("WM",         get_wm()),
        fmt_row("Terminal",   get_terminal()),
        fmt_row("Shell",      get_shell()),
        "",
        f"  {GRAY}{'─' * 28}{RESET}",
        # Цветовые блоки
        "  " + "".join(
            f"\033[4{c}m   \033[0m" for c in range(8)
        ),
        "",
    ]

    # Выравниваем кот + текст по строкам
    # Ширина блока кота (в символах без escape-кодов) = max len в CAT
    cat_width = max(len(line) for line in CAT)

    total_rows = max(len(CAT), len(info_lines))

    for i in range(total_rows):
        cat_part  = CAT[i]       if i < len(CAT)        else ""
        info_part = info_lines[i] if i < len(info_lines) else ""
        # Дополняем кота пробелами до фиксированной ширины
        cat_padded = f"{PINK}{cat_part:<{cat_width}}{RESET}"
        print(cat_padded + "  " + info_part)


# ──────────────────────────────────────────────
if __name__ == "__main__":
    render()
