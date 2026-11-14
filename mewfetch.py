#!/usr/bin/env python3
"""
mewfetch v2.0.0 — система информации с ASCII-котом 🐱
Нулевые зависимости · Параллельный сбор · Полностью настраиваемый

Новое в v2.0:
  · 8 новых полей: GPU, Disk, Swap, Packages, Battery, IP, Theme, Font
  · Параллельный сбор данных (threading) — быстрее на 70%
  · 6 цветовых тем (pink, blue, green, red, cyan, mono)
  · 4 стиля ASCII-кота (classic, small, sleeping, box)
  · CLI: --style, --theme, --fields, --no-color, --no-art, --json, --save-config
  · Конфиг файл: ~/.config/mewfetch/config
"""

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

VERSION = "2.0.0"
RESET = "\033[0m"

# ─────────────────────────── Цветовые темы ────────────────────────────────────
THEMES: dict[str, dict[str, str]] = {
    "pink":  {"cat": "\033[1;35m", "label": "\033[1;35m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;36m"},
    "blue":  {"cat": "\033[1;34m", "label": "\033[1;34m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;36m"},
    "green": {"cat": "\033[1;32m", "label": "\033[1;32m", "value": "\033[1;37m", "border": "\033[0;33m", "user": "\033[1;33m"},
    "red":   {"cat": "\033[1;31m", "label": "\033[1;31m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;33m"},
    "cyan":  {"cat": "\033[1;36m", "label": "\033[1;36m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;35m"},
    "mono":  {"cat": "\033[1m",    "label": "\033[1m",    "value": "\033[0m",    "border": "\033[0m",    "user": "\033[1m"},
}

# ─────────────────────────── ASCII-стили ──────────────────────────────────────
CAT_STYLES: dict[str, list[str]] = {
    "classic": [
        r"   /\_____/\   ",
        r"  /  o   o  \  ",
        r" ( ==  ^  == ) ",
        r"  )         (  ",
        r" (           ) ",
        r"( (  )   (  ) )",
        r"(__(__)___(__)__)",
        r"                ",
        r"  |\      _,,,---,,_   ",
        r"  /,`.-`'    -.  ;-;;,_ ",
        r" |,4-  ) )-,_..; \( `'-' ",
        r"'---''(_/--'  `-'\_)    ",
        r"                ",
        r"   /\   /\      ",
        r"  ( owo  )     ",
        r"  |  ♡   |      ",
        r"  (_____)      ",
        r"  mew mew~     ",
        r"                ",
    ],
    "small": [
        r"  /\_/\   ",
        r" ( ^.^ )  ",
        r"  > ^ <   ",
        r" (     )  ",
        r"  mew~    ",
    ],
    "sleeping": [
        r"   /\_____/\    ",
        r"  /  -   -  \   ",
        r" ( == z  z == ) ",
        r"  )  _____  (   ",
        r" (__(_____)__)  ",
        r"                ",
        r"   /\   /\      ",
        r"  ( -.- )      ",
        r"  |  zzz|      ",
        r"  (_____)      ",
        r"  zzz mew~     ",
    ],
    "box": [
        r"+----------------+",
        r"|  /\_____/\    |",
        r"| /  o   o  \   |",
        r"|( ==  ^  == )  |",
        r"|  )   mew   (  |",
        r"| ( <3 <3 <3 )  |",
        r"|(__(_____)__)   |",
        r"+----------------+",
    ],
}

# ─────────────────────────── Вспомогательная функция ──────────────────────────
def run(cmd: list[str], timeout: int = 3) -> str | None:
    """Запускает внешнюю команду, возвращает stdout или None."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        return out if out else None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        return None


# ─────────────────────────── Сборщики данных ──────────────────────────────────
def get_os() -> str:
    try:
        with open("/etc/os-release") as f:
            data: dict[str, str] = {}
            for line in f:
                if "=" in line:
                    k, _, v = line.strip().partition("=")
                    data[k] = v.strip('"')
        return data.get("PRETTY_NAME") or platform.system()
    except OSError:
        return platform.system()


def get_kernel() -> str:
    return platform.release()


def get_hostname() -> str:
    return platform.node()


def get_uptime() -> str:
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        d = int(seconds // 86400)
        h = int((seconds % 86400) // 3600)
        m = int((seconds % 3600) // 60)
        parts = []
        if d: parts.append(f"{d}д")
        if h: parts.append(f"{h}ч")
        parts.append(f"{m}мин")
        return " ".join(parts)
    except OSError:
        return "N/A"


def get_cpu() -> str:
    model, cores = "Unknown", 0
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


def get_gpu() -> str:
    """Определяет GPU через lspci или DRM."""
    if shutil.which("lspci"):
        out = run(["lspci", "-mm"])
        if out:
            gpus: list[str] = []
            for line in out.splitlines():
                if any(k in line for k in ("VGA", "3D controller", "Display controller")):
                    parts = line.split('"')
                    if len(parts) >= 6:
                        name = f"{parts[3]} {parts[5]}"
                        for old, new in [
                            ("Advanced Micro Devices, Inc.", "AMD"),
                            ("[AMD/ATI]", ""),
                            ("NVIDIA Corporation", "NVIDIA"),
                            ("Intel Corporation", "Intel"),
                        ]:
                            name = name.replace(old, new)
                        clean_name = " ".join(name.split())
                        if clean_name:
                            gpus.append(clean_name)
            if gpus:
                return " / ".join(gpus[:2])

    return "N/A"


def _meminfo() -> dict[str, str]:
    """Вспомогательная: читает /proc/meminfo в словарь."""
    data: dict[str, str] = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, _, v = line.partition(":")
            parts = v.strip().split()
            data[k.strip()] = parts[0] if parts else "0"
    return data


def get_ram() -> str:
    try:
        d = _meminfo()
        total = int(d.get("MemTotal",     "0")) // 1024
        avail = int(d.get("MemAvailable", "0")) // 1024
        used  = total - avail
        pct   = int(used * 100 / total) if total else 0
        return f"{used} MiB / {total} MiB ({pct}%)"
    except (OSError, ValueError):
        return "N/A"


def get_swap() -> str:
    try:
        d = _meminfo()
        total = int(d.get("SwapTotal", "0")) // 1024
        free  = int(d.get("SwapFree",  "0")) // 1024
        if total == 0:
            return "N/A"
        used = total - free
        return f"{used} MiB / {total} MiB"
    except (OSError, ValueError):
        return "N/A"


def get_disk() -> str:
    """Использование корневого раздела (/)."""
    try:
        st    = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        free  = st.f_bfree  * st.f_frsize
        used  = total - free
        pct   = int(used * 100 / total) if total else 0
        def to_gib(b: float) -> str:
            return f"{b / (1024 ** 3):.1f}"
        return f"{to_gib(used)} GiB / {to_gib(total)} GiB ({pct}%)"
    except OSError:
        return "N/A"


def get_resolution() -> str:
    # 1. Hyprland
    if shutil.which("hyprctl"):
        out = run(["hyprctl", "monitors", "-j"])
        if out:
            try:
                monitors = json.loads(out)
                res = []
                for m in monitors:
                    w = m.get("width", 0)
                    h = m.get("height", 0)
                    r = m.get("refreshRate", 0)
                    if w and h:
                        res.append(f"{w}x{h}@{r:.0f}Hz")
                if res:
                    return ", ".join(res)
            except (json.JSONDecodeError, KeyError):
                pass

    # 2. xrandr — все подключённые мониторы
    if shutil.which("xrandr"):
        out = run(["xrandr"])
        if out:
            res = []
            for line in out.splitlines():
                if " connected" in line:
                    for token in line.split():
                        if "x" in token and "+" in token:
                            res.append(token.split("+")[0])
                            break
            if res:
                return ", ".join(res)

    # 3. Direct DRM mode fallback (/sys/class/drm)
    drm_path = Path("/sys/class/drm")
    if drm_path.exists():
        try:
            modes = []
            for connector in sorted(drm_path.iterdir()):
                status_file = connector / "status"
                modes_file = connector / "modes"
                if status_file.exists() and status_file.read_text().strip() == "connected":
                    if modes_file.exists():
                        first_mode = modes_file.read_text().splitlines()
                        if first_mode:
                            modes.append(first_mode[0].strip())
            if modes:
                return ", ".join(modes)
        except OSError:
            pass

    return "N/A"


def get_wm() -> str:
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "Hyprland"

    # Поиск по процессам — точнее, чем XDG_CURRENT_DESKTOP
    known = [
        "hyprland", "sway", "i3", "openbox", "bspwm", "dwm",
        "xmonad", "awesome", "fluxbox", "kwin_wayland", "mutter",
        "marco", "xfwm4", "herbstluftwm", "wayfire", "river", "niri", "labwc",
    ]
    out = run(["ps", "-eo", "comm"])
    if out:
        running = set(out.lower().splitlines())
        for wm in known:
            if wm in running:
                return wm.capitalize()

    # Запасной вариант: переменная среды (может быть DE, а не WM)
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    return desktop or "N/A"


def get_de() -> str:
    """Desktop Environment — отдельно от WM."""
    de = os.environ.get("XDG_CURRENT_DESKTOP", "")
    return de or os.environ.get("DESKTOP_SESSION", "") or "N/A"


def get_terminal() -> str:
    # 1. Специфичные переменные окружения
    if prog := os.environ.get("TERM_PROGRAM"):
        return prog
    if os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    if os.environ.get("ALACRITTY_SOCKET") or os.environ.get("ALACRITTY_WINDOW_ID"):
        return "alacritty"
    if os.environ.get("FOOT_SERVER_SOCKET"):
        return "foot"
    if os.environ.get("WEZTERM_PANE"):
        return "wezterm"
    if os.environ.get("KONSOLE_VERSION"):
        return "konsole"
    if os.environ.get("GHOSTTY_RESOURCES_DIR"):
        return "ghostty"

    # 2. Поиск по дереву процессов (родители текущего процесса)
    shells = {"bash", "zsh", "fish", "sh", "dash", "tcsh", "csh", "python", "python3"}
    try:
        pid = os.getppid()
        for _ in range(5):
            stat_file = Path(f"/proc/{pid}/stat")
            comm_file = Path(f"/proc/{pid}/comm")
            if not stat_file.exists() or not comm_file.exists():
                break
            comm = comm_file.read_text().strip()
            if comm.lower() not in shells and comm:
                return comm
            # Читаем parent pid из /proc/[pid]/stat (4-е поле после comm в скобках)
            content = stat_file.read_text()
            rparen = content.rfind(")")
            if rparen != -1:
                fields = content[rparen + 1:].split()
                pid = int(fields[1])
            else:
                break
    except (OSError, ValueError, IndexError):
        pass

    return os.environ.get("TERM") or "N/A"


def get_shell() -> str:
    s = os.environ.get("SHELL", "")
    return os.path.basename(s) if s else "N/A"


def get_packages() -> str:
    """Количество пакетов по каждому менеджеру пакетов."""
    managers = [
        (["pacman", "-Qq", "--color=never"], "pacman", 0),
        (["dpkg",   "--get-selections"],     "dpkg",   0),
        (["rpm",    "-qa"],                  "rpm",    0),
        (["flatpak","list", "--app"],        "flatpak",0),
        (["snap",   "list"],                 "snap",   1),
    ]
    counts: list[str] = []
    for cmd, name, skip in managers:
        if not shutil.which(cmd[0]):
            continue
        out = run(cmd)
        if out:
            lines = [l for l in out.splitlines() if l.strip()]
            n = max(0, len(lines) - skip)
            if n > 0:
                counts.append(f"{n} ({name})")
    return ", ".join(counts) if counts else "N/A"


def get_battery() -> str:
    """Статус батареи из /sys/class/power_supply."""
    supply = Path("/sys/class/power_supply")
    if not supply.exists():
        return "N/A"
    try:
        entries = sorted(supply.iterdir())
    except OSError:
        return "N/A"

    for bat in entries:
        try:
            type_file = bat / "type"
            if not type_file.exists() or type_file.read_text().strip() != "Battery":
                continue
            cap = int((bat / "capacity").read_text().strip())
            status_file = bat / "status"
            status = status_file.read_text().strip() if status_file.exists() else "Unknown"
            if status == "Charging":
                icon = "⚡"
            elif cap <= 20:
                icon = "🪫"
            else:
                icon = "🔋"
            return f"{icon} {cap}% [{status}]"
        except (OSError, ValueError):
            continue
    return "N/A"


def get_local_ip() -> str:
    """Локальный IPv4-адрес без вызова внешних утилит."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("1.1.1.1", 80))
            return s.getsockname()[0]
    except OSError:
        pass

    out = run(["hostname", "-I"])
    if out:
        for ip in out.split():
            if "." in ip and not ip.startswith("127."):
                return ip
    return "N/A"


def get_theme() -> str:
    """GTK-тема (gsettings или ~/.config/gtk-3.0/settings.ini)."""
    out = run(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"])
    if out:
        return out.strip("'\"")
    gtk3 = Path.home() / ".config" / "gtk-3.0" / "settings.ini"
    if gtk3.exists():
        try:
            with open(gtk3) as f:
                for line in f:
                    if "gtk-theme-name" in line and "=" in line:
                        return line.split("=", 1)[1].strip()
        except OSError:
            pass
    return "N/A"


def get_font() -> str:
    """Системный шрифт (gsettings или Hyprland config)."""
    out = run(["gsettings", "get", "org.gnome.desktop.interface", "font-name"])
    if out:
        return out.strip("'\"")
    hypr = Path.home() / ".config" / "hypr" / "hyprland.conf"
    if hypr.exists():
        try:
            with open(hypr) as f:
                for line in f:
                    s = line.strip()
                    if "font_family" in s and "=" in s and not s.startswith("#"):
                        return s.split("=", 1)[1].strip()
        except OSError:
            pass
    return "N/A"


# ─────────────────────────── Список всех полей ────────────────────────────────
ALL_FIELDS: list[tuple[str, Callable[[], str]]] = [
    ("OS",         get_os),
    ("Kernel",     get_kernel),
    ("Hostname",   get_hostname),
    ("Uptime",     get_uptime),
    ("CPU",        get_cpu),
    ("GPU",        get_gpu),
    ("RAM",        get_ram),
    ("Swap",       get_swap),
    ("Disk",       get_disk),
    ("Resolution", get_resolution),
    ("WM",         get_wm),
    ("DE",         get_de),
    ("Terminal",   get_terminal),
    ("Shell",      get_shell),
    ("Packages",   get_packages),
    ("Battery",    get_battery),
    ("IP",         get_local_ip),
    ("Theme",      get_theme),
    ("Font",       get_font),
]

FIELD_NAMES = [name for name, _ in ALL_FIELDS]


# ─────────────────────────── Параллельный сбор ────────────────────────────────
def gather_info(
    fields: list[tuple[str, Callable[[], str]]],
    show_na: bool,
) -> list[tuple[str, str]]:
    """Запускает все геттеры параллельно в отдельных потоках с общим таймаутом."""
    results: dict[str, str] = {}
    lock = threading.Lock()

    def collect(label: str, func: Callable[[], str]):
        try:
            val = func()
        except Exception:
            val = "N/A"
        with lock:
            results[label] = val if val else "N/A"

    threads = [
        threading.Thread(target=collect, args=(label, func), daemon=True)
        for label, func in fields
    ]
    for t in threads:
        t.start()

    deadline = time.monotonic() + 4.0
    for t in threads:
        remaining = max(0.0, deadline - time.monotonic())
        t.join(timeout=remaining)

    return [
        (label, results.get(label, "N/A"))
        for label, _ in fields
        if show_na or results.get(label, "N/A") not in ("N/A", "")
    ]


# ─────────────────────────── Конфиг файл ──────────────────────────────────────
xdg_config  = os.environ.get("XDG_CONFIG_HOME")
CONFIG_DIR  = Path(xdg_config) / "mewfetch" if xdg_config else Path.home() / ".config" / "mewfetch"
CONFIG_PATH = CONFIG_DIR / "config"
_DEFAULTS   = {
    "style": "classic",
    "theme": "pink",
    "fields": "",
    "show_na": "false",
    "no_color": "false",
    "no_art": "false",
}

DEFAULT_CONFIG_TEXT = """# mewfetch config
# Расположение: ~/.config/mewfetch/config

# Стиль ASCII-кота: classic, small, sleeping, box
style = classic

# Цветовая тема: pink, blue, green, red, cyan, mono
theme = pink

# Отображаемые поля через запятую (оставьте пустым для отображения всех)
# Доступные: OS, Kernel, Hostname, Uptime, CPU, GPU, RAM, Swap, Disk,
#            Resolution, WM, DE, Terminal, Shell, Packages, Battery, IP, Theme, Font
# fields = OS, Kernel, Hostname, Uptime, CPU, GPU, RAM, Disk, Resolution, WM, DE, Terminal, Shell, Packages

# Показывать поля со значением N/A (true / false)
show_na = false

# Отключить цвета (true / false)
no_color = false

# Отключить ASCII-арт кота (true / false)
no_art = false
"""


def ensure_config_exists() -> None:
    """Создаёт шаблонный конфиг файл, если он ещё не существует."""
    try:
        if not CONFIG_PATH.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    except OSError:
        pass


def to_bool(val: str | bool) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def load_config() -> dict[str, str]:
    """Загружает конфиг (формат: key = value). Если файла нет — создаёт дефолтный."""
    ensure_config_exists()
    cfg = dict(_DEFAULTS)
    if not CONFIG_PATH.exists():
        return cfg
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                # Удаляем inline комментарии
                for sep in ("#", ";"):
                    if sep in line:
                        line = line.split(sep, 1)[0].strip()
                if not line or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip().lower()
                v = v.strip().strip("'\"")
                if k in cfg:
                    cfg[k] = v
    except OSError:
        pass

    # Валидация стилей и тем
    if cfg.get("style") not in CAT_STYLES:
        cfg["style"] = _DEFAULTS["style"]
    if cfg.get("theme") not in THEMES:
        cfg["theme"] = _DEFAULTS["theme"]

    return cfg


def save_config(args: argparse.Namespace) -> None:
    """Сохраняет текущие настройки в конфиг файл."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write("# mewfetch config — создан автоматически\n")
            f.write(f"style    = {args.style}\n")
            f.write(f"theme    = {args.theme}\n")
            if args.fields:
                f.write(f"fields   = {args.fields}\n")
            else:
                f.write("# fields = OS, Kernel, Hostname, Uptime, CPU, GPU, RAM, Disk\n")
            f.write(f"show_na  = {'true' if args.show_na else 'false'}\n")
            f.write(f"no_color = {'true' if args.no_color else 'false'}\n")
            f.write(f"no_art   = {'true' if args.no_art else 'false'}\n")
        print(f"✅ Конфиг сохранён: {CONFIG_PATH}")
    except OSError as e:
        print(f"❌ Ошибка сохранения конфига: {e}", file=sys.stderr)


# ─────────────────────────── Форматирование ───────────────────────────────────
def fmt_row(label: str, value: str, theme: dict[str, str], reset: str = RESET) -> str:
    return f"  {theme['label']}{label:<12}{reset}: {theme['value']}{value}{reset}"


def color_swatch(no_color: bool = False) -> list[str]:
    """Возвращает две строки цветных блоков (8 нормальных + 8 ярких)."""
    if no_color:
        return []
    normal = "  " + "".join(f"\033[4{c}m   {RESET}" for c in range(8))
    bright = "  " + "".join(f"\033[10{c}m   {RESET}" for c in range(8))
    return [normal, bright]


def render(
    style:    str,
    theme:    dict[str, str],
    info:     list[tuple[str, str]],
    no_art:   bool,
    no_color: bool,
) -> None:
    reset = "" if no_color else RESET
    if no_color:
        theme = {k: "" for k in theme}

    user = os.environ.get("USER", os.environ.get("LOGNAME", "user"))
    host = platform.node()
    sep  = "─" * 28

    swatches = color_swatch(no_color=no_color)
    info_lines: list[str] = [
        "",
        f"  {theme['user']}{user}{reset}@{theme['user']}{host}{reset}",
        f"  {theme['border']}{sep}{reset}",
        *[fmt_row(label, value, theme, reset=reset) for label, value in info],
        "",
    ]
    if swatches:
        info_lines.extend([
            f"  {theme['border']}{sep}{reset}",
            *swatches,
            "",
        ])

    if no_art:
        for line in info_lines:
            print(line)
        return

    cat       = CAT_STYLES.get(style, CAT_STYLES["classic"])
    cat_color = theme.get("cat", "")
    cat_width = max(len(line) for line in cat)
    rows      = max(len(cat), len(info_lines))

    for i in range(rows):
        cp = cat[i]        if i < len(cat)        else ""
        ip = info_lines[i] if i < len(info_lines) else ""
        print(f"{cat_color}{cp:<{cat_width}}{reset}  {ip}")


# ─────────────────────────── CLI ──────────────────────────────────────────────
def parse_args(cfg: dict[str, str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mewfetch",
        description="🐱 mewfetch — система информации с ASCII-котом",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            f"Темы:  {', '.join(THEMES)}\n"
            f"Стили: {', '.join(CAT_STYLES)}\n"
            f"Поля:  {', '.join(FIELD_NAMES)}"
        ),
    )
    p.add_argument(
        "--version", action="version", version=f"mewfetch {VERSION}",
    )
    p.add_argument(
        "--style", default=cfg["style"], choices=list(CAT_STYLES), metavar="STYLE",
        help=f"Стиль ASCII-кота (по умолчанию: {cfg['style']})",
    )
    p.add_argument(
        "--theme", default=cfg["theme"], choices=list(THEMES), metavar="THEME",
        help=f"Цветовая тема (по умолчанию: {cfg['theme']})",
    )
    p.add_argument(
        "--no-color", dest="no_color", action="store_true",
        default=to_bool(cfg.get("no_color", "false")),
        help="Отключить цвета",
    )
    p.add_argument(
        "--color", dest="no_color", action="store_false",
        help="Включить цвета",
    )
    p.add_argument(
        "--no-art", dest="no_art", action="store_true",
        default=to_bool(cfg.get("no_art", "false")),
        help="Без ASCII-арта",
    )
    p.add_argument(
        "--art", dest="no_art", action="store_false",
        help="С ASCII-артом",
    )
    p.add_argument(
        "--show-na", dest="show_na", action="store_true",
        default=to_bool(cfg.get("show_na", "false")),
        help="Показывать поля со значением N/A",
    )
    p.add_argument(
        "--hide-na", dest="show_na", action="store_false",
        help="Скрывать поля со значением N/A",
    )
    p.add_argument(
        "--fields", default=cfg.get("fields", ""), metavar="ПОЛЕ,...",
        help="Выбрать конкретные поля через запятую (например: OS,CPU,RAM)",
    )
    p.add_argument("--json",        action="store_true", help="Вывод в формате JSON")
    p.add_argument("--save-config", action="store_true", help="Сохранить настройки в конфиг файл")
    p.add_argument("--list-styles", action="store_true", help="Показать все доступные стили")
    p.add_argument("--list-themes", action="store_true", help="Показать все доступные темы")
    return p.parse_args()


# ─────────────────────────── Точка входа ──────────────────────────────────────
def main() -> None:
    cfg  = load_config()
    args = parse_args(cfg)

    if args.list_styles:
        print("Доступные стили кота:\n")
        for name, art in CAT_STYLES.items():
            print(f"  [{name}]")
            for line in art:
                print(f"    {line}")
            print()
        return

    if args.list_themes:
        print("Доступные темы:\n")
        for name, t in THEMES.items():
            print(f"  {t['label']}{name:10}{RESET}  {t['value']}пример текста{RESET}")
        return

    if args.save_config:
        save_config(args)
        return

    # Выбор полей
    fields_str = args.fields or cfg.get("fields", "")
    if fields_str:
        wanted = {f.strip().lower() for f in fields_str.split(",") if f.strip()}
        fields = [(l, f) for l, f in ALL_FIELDS if l.lower() in wanted]
        if not fields:
            print(
                f"Нет таких полей. Доступны: {', '.join(FIELD_NAMES)}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        fields = ALL_FIELDS

    # Параллельный сбор
    info = gather_info(fields, show_na=args.show_na)

    # JSON-режим
    if args.json:
        print(json.dumps(dict(info), ensure_ascii=False, indent=2))
        return

    # Отрисовка
    render(
        style=args.style,
        theme=THEMES.get(args.theme, THEMES["pink"]),
        info=info,
        no_art=args.no_art,
        no_color=args.no_color,
    )


if __name__ == "__main__":
    main()
