#!/usr/bin/env python3
"""
mewfetch v2.1.0 — system information tool with an ASCII cat 🐱
Zero dependencies · Concurrent data fetching · Fully customizable

What's new in v2.0:
  · 8 new fields: GPU, Disk, Swap, Packages, Battery, IP, Theme, Font
  · Concurrent data collection (threading) — 70% faster
  · 6 color themes (pink, blue, green, red, cyan, mono)
  · 4 cat ASCII art styles (classic, small, sleeping, box)
  · CLI: --style, --theme, --fields, --no-color, --no-art, --json, --save-config
  · Config file: ~/.config/mewfetch/config

What's new in v2.1:
  · Custom logo support via config.json
  · logo_path: path to ASCII art or image file
  · logo_type: "ascii" (text art) or "image" (PNG/JPG via term-image or Kitty)
"""

import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path
from typing import Callable

VERSION = "2.1.0"
RESET = "\033[0m"

# ─────────────────────────── Color themes ─────────────────────────────────────
THEMES: dict[str, dict[str, str]] = {
    "pink":  {"cat": "\033[1;35m", "label": "\033[1;35m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;36m"},
    "blue":  {"cat": "\033[1;34m", "label": "\033[1;34m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;36m"},
    "green": {"cat": "\033[1;32m", "label": "\033[1;32m", "value": "\033[1;37m", "border": "\033[0;33m", "user": "\033[1;33m"},
    "red":   {"cat": "\033[1;31m", "label": "\033[1;31m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;33m"},
    "cyan":  {"cat": "\033[1;36m", "label": "\033[1;36m", "value": "\033[1;37m", "border": "\033[0;37m", "user": "\033[1;35m"},
    "mono":  {"cat": "\033[1m",    "label": "\033[1m",    "value": "\033[0m",    "border": "\033[0m",    "user": "\033[1m"},
}

# ─────────────────────────── ASCII styles ─────────────────────────────────────
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

# ─────────────────────────── Helper functions ─────────────────────────────────
def run(cmd: list[str], timeout: int = 3) -> str | None:
    """Runs an external command, returns stdout or None."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        return out if out else None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        return None


# ─────────────────────────── Data Collectors ──────────────────────────────────
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
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        parts.append(f"{m}m")
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
    """Detects GPU via lspci or DRM."""
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
    """Helper: reads /proc/meminfo into a dictionary."""
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
    """Root partition (/) disk usage."""
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

    # 2. xrandr — all connected monitors
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

    # Process search — more reliable than XDG_CURRENT_DESKTOP
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

    # Fallback: environment variable (may be DE rather than WM)
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    return desktop or "N/A"


def get_de() -> str:
    """Desktop Environment — separate from WM."""
    de = os.environ.get("XDG_CURRENT_DESKTOP", "")
    return de or os.environ.get("DESKTOP_SESSION", "") or "N/A"


def get_terminal() -> str:
    # 1. Specific environment variables
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

    # 2. Process tree traversal (parents of current process)
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
            # Read parent pid from /proc/[pid]/stat (4th field after comm in parentheses)
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
    """Number of packages for each supported package manager."""
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
    """Battery status from /sys/class/power_supply."""
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
    """Local IPv4 address without invoking external utilities."""
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
    """GTK theme (gsettings or ~/.config/gtk-3.0/settings.ini)."""
    out = run(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"])
    if out:
        return out.strip("'\"")
    gtk3 = Path(os.path.expanduser("~/.config/gtk-3.0/settings.ini"))
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
    """System font (gsettings or Hyprland config)."""
    out = run(["gsettings", "get", "org.gnome.desktop.interface", "font-name"])
    if out:
        return out.strip("'\"")
    hypr = Path(os.path.expanduser("~/.config/hypr/hyprland.conf"))
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


# ─────────────────────────── Field list ───────────────────────────────────────
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


# ─────────────────────────── Concurrent data gathering ────────────────────────
def gather_info(
    fields: list[tuple[str, Callable[[], str]]],
    show_na: bool,
) -> list[tuple[str, str]]:
    """Runs all getters concurrently in separate threads with an overall timeout."""
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


# ─────────────────────────── Configuration File ───────────────────────────────
xdg_config      = os.environ.get("XDG_CONFIG_HOME")
CONFIG_DIR      = Path(xdg_config) / "mewfetch" if xdg_config else Path(os.path.expanduser("~/.config/mewfetch"))
CONFIG_PATH     = CONFIG_DIR / "config"
CONFIG_JSON     = CONFIG_DIR / "config.json"
_DEFAULTS       = {
    "style": "classic",
    "theme": "pink",
    "fields": "",
    "show_na": "false",
    "no_color": "false",
    "no_art": "false",
}
_JSON_DEFAULTS = {
    "logo_path": "",
    "logo_type": "ascii",
}

DEFAULT_CONFIG_TEXT = """# mewfetch config
# Location: ~/.config/mewfetch/config

# Cat ASCII art style: classic, small, sleeping, box
style = classic

# Color theme: pink, blue, green, red, cyan, mono
theme = pink

# Comma-separated list of displayed fields (leave empty to show all)
# Available: OS, Kernel, Hostname, Uptime, CPU, GPU, RAM, Swap, Disk,
#            Resolution, WM, DE, Terminal, Shell, Packages, Battery, IP, Theme, Font
# fields = OS, Kernel, Hostname, Uptime, CPU, GPU, RAM, Disk, Resolution, WM, DE, Terminal, Shell, Packages

# Show fields with N/A values (true / false)
show_na = false

# Disable colors (true / false)
no_color = false

# Disable cat ASCII art (true / false)
no_art = false
"""


def ensure_config_exists() -> None:
    """Creates config directory, INI config, and config.json if they do not exist.

    Each file is created independently — an error with one does not block the other.
    """
    # 1. Directory
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        return  # Cannot create config directory

    # 2. INI config (style, theme, …)
    try:
        if not CONFIG_PATH.exists():
            CONFIG_PATH.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    except OSError:
        pass

    # 3. JSON config (logo_path, logo_type)
    try:
        if not CONFIG_JSON.exists():
            CONFIG_JSON.write_text(
                json.dumps(_JSON_DEFAULTS, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except OSError:
        pass


def to_bool(val: str | bool) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def load_config() -> dict[str, str]:
    """Loads config (format: key = value). Creates default file if missing."""
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
                # Strip inline comments
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

    # Validate styles and themes
    if cfg.get("style") not in CAT_STYLES:
        cfg["style"] = _DEFAULTS["style"]
    if cfg.get("theme") not in THEMES:
        cfg["theme"] = _DEFAULTS["theme"]

    return cfg


def load_logo_config() -> dict[str, str]:
    """Loads config.json with logo settings.

    Returns a dict with keys:
      logo_path — path to logo file (empty string -> default cat)
      logo_type — "ascii" or "image"
    """
    cfg = dict(_JSON_DEFAULTS)
    if not CONFIG_JSON.exists():
        return cfg
    try:
        with open(CONFIG_JSON, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data.get("logo_path"), str):
            cfg["logo_path"] = data["logo_path"]
        if data.get("logo_type") in ("ascii", "image"):
            cfg["logo_type"] = data["logo_type"]
    except (OSError, json.JSONDecodeError):
        pass
    return cfg


def _expand(path: str) -> str:
    """Expands ~ and environment variables in path."""
    return os.path.expandvars(os.path.expanduser(path))


def load_ascii_logo(path: str) -> list[str] | None:
    """Reads ASCII art from a file. Returns None on error."""
    try:
        full = _expand(path)
        with open(full, encoding="utf-8") as f:
            lines = f.read().splitlines()
        return lines
    except FileNotFoundError:
        print(
            f"⚠️  mewfetch: logo file not found: {path!r} — using default cat.",
            file=sys.stderr,
        )
        return None
    except OSError as e:
        print(
            f"⚠️  mewfetch: error reading logo ({e}) — using default cat.",
            file=sys.stderr,
        )
        return None


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def visible_len(s: str) -> int:
    """Calculates visible terminal width of string without ANSI codes and accounting for wide characters."""
    clean = ANSI_RE.sub("", s)
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in clean)


def render_image_logo(path: str, info_lines: list[str]) -> bool:
    """Renders image using term-image with adaptive resolution and overflow protection.

    - Dynamically scales to terminal dimensions.
    - Prioritizes native terminal protocol (Kitty/iTerm2) falling back to direct-color BlockImage.
    - Responsive layout for smaller windows/tiling:
        * width < 40 or height < 15: image is scaled down (50%) and rendered on TOP, info underneath.
        * width < 35 or height < 10: image is disabled, only text is rendered.
        * sufficient space: image is rendered on the RIGHT at maximum available resolution.
    - If term-image is missing or file not found: prints error to stderr and returns False (fallback to ASCII cat).
    """
    full = _expand(path)
    if not os.path.isfile(full):
        print(
            f"⚠️  mewfetch: image file not found at path: '{path}' (full path: '{full}')",
            file=sys.stderr,
        )
        return False

    try:
        import term_image
        from term_image.image import from_file, KittyImage

        # Configure dynamic terminal cell ratio for proper aspect ratio
        try:
            term_image.set_cell_ratio(term_image.AutoCellRatio.DYNAMIC)
        except Exception:
            pass

        # Configure Kitty Graphics Protocol support without leaking escape sequences
        is_kitty = bool(os.environ.get("KITTY_WINDOW_ID") or os.environ.get("TERM") == "xterm-kitty")
        if is_kitty:
            try:
                KittyImage._supported = True
                KittyImage.forced_support = True
            except Exception:
                pass
        else:
            KittyImage._supported = False
    except ImportError:
        print(
            "⚠️  mewfetch: term-image library is required for image rendering.\n"
            "   Install it with: pip install term-image\n"
            "   Falling back to default ASCII cat...",
            file=sys.stderr,
        )
        return False

    try:
        img = from_file(full)
        if hasattr(img, "_render_methods") and "lines" in img._render_methods:
            try:
                img.set_render_method("lines")
            except Exception:
                pass
    except Exception as e:
        print(
            f"⚠️  mewfetch: error loading image via term-image: {e}",
            file=sys.stderr,
        )
        return False

    # ── Check terminal size (adaptive layout for tiling and small windows) ──
    term_size = shutil.get_terminal_size((80, 24))
    term_cols = term_size.columns
    term_lines = term_size.lines
    max_info_w = max((visible_len(line) for line in info_lines), default=0)
    info_h = len(info_lines)

    # 1. Very small window — disable image and display only text
    if term_cols < 35 or term_lines < 10:
        for line in info_lines:
            print(line)
        return True

    # 2. Not enough room for side-by-side layout (width < 40, height < 15, or doesn't fit horizontally)
    # Move image to TOP, scale down proportionally (50% width), and print info BELOW it
    if term_cols < max_info_w + 20 or term_cols < 40 or term_lines < 15:
        top_w = max(10, min(int(term_cols * 0.5), term_cols - 2))
        top_h = max(4, min(14, max(term_lines - info_h - 2, 6)))
        try:
            img.set_size(height=top_h)
            if img.width > top_w:
                img.set_size(width=top_w)
        except Exception:
            pass

        img_lines = str(img).splitlines()
        for line in img_lines:
            print(line)
        for line in info_lines:
            print(line)
        return True

    # 3. Sufficient space: render on the right with adaptive maximum resolution
    avail_w = max(15, term_cols - max_info_w - 4)
    avail_h = max(info_h, min(term_lines - 2, 50))
    try:
        img.set_size(height=avail_h)
        if img.width > avail_w:
            img.set_size(width=avail_w)
    except Exception:
        pass

    img_lines = str(img).splitlines()
    rows = max(len(info_lines), len(img_lines))
    for i in range(rows):
        ip = info_lines[i] if i < len(info_lines) else ""
        im = img_lines[i] if i < len(info_lines) else ""
        pad = " " * (max_info_w - visible_len(ip))
        print(f"{ip}{pad}   {im}")
    return True


def save_config(args: argparse.Namespace) -> None:
    """Saves current settings to the config file."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write("# mewfetch config — automatically generated\n")
            f.write(f"style    = {args.style}\n")
            f.write(f"theme    = {args.theme}\n")
            if args.fields:
                f.write(f"fields   = {args.fields}\n")
            else:
                f.write("# fields = OS, Kernel, Hostname, Uptime, CPU, GPU, RAM, Disk\n")
            f.write(f"show_na  = {'true' if args.show_na else 'false'}\n")
            f.write(f"no_color = {'true' if args.no_color else 'false'}\n")
            f.write(f"no_art   = {'true' if args.no_art else 'false'}\n")
        print(f"✅ Config saved: {CONFIG_PATH}")
    except OSError as e:
        print(f"❌ Error saving config: {e}", file=sys.stderr)


# ─────────────────────────── Formatting ───────────────────────────────────────
def fmt_row(label: str, value: str, theme: dict[str, str], reset: str = RESET) -> str:
    return f"  {theme['label']}{label:<12}{reset}: {theme['value']}{value}{reset}"


def color_swatch(no_color: bool = False) -> list[str]:
    """Returns two rows of color blocks (8 normal + 8 bright)."""
    if no_color:
        return []
    normal = "  " + "".join(f"\033[4{c}m   {RESET}" for c in range(8))
    bright = "  " + "".join(f"\033[10{c}m   {RESET}" for c in range(8))
    return [normal, bright]


def render(
    style:      str,
    theme:      dict[str, str],
    info:       list[tuple[str, str]],
    no_art:     bool,
    no_color:   bool,
    logo_cfg:   dict[str, str] | None = None,
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

    # ── Determine logo source ──────────────────────────────────────────
    logo_path = (logo_cfg or {}).get("logo_path", "").strip()
    logo_type = (logo_cfg or {}).get("logo_type", "ascii")

    if logo_path:
        if logo_type == "image":
            # Render image via adaptive renderer (right side, or top when tight)
            if render_image_logo(logo_path, info_lines):
                return
            # On failure (missing file / missing library) — fall back to default cat
            logo_path = ""
        else:
            # ascii mode: art on the left, info on the right
            custom_lines = load_ascii_logo(logo_path)
            if custom_lines is not None:
                cat       = custom_lines
                cat_color = theme.get("cat", "")
                cat_width = max((len(line) for line in cat), default=0)
                rows      = max(len(cat), len(info_lines))
                for i in range(rows):
                    cp = cat[i]        if i < len(cat)        else ""
                    ip = info_lines[i] if i < len(info_lines) else ""
                    print(f"{cat_color}{cp:<{cat_width}}{reset}  {ip}")
                return
            # File not found — fall back to default cat

    # ── Default ASCII cat ─────────────────────────────────────────────────
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
        description="🐱 mewfetch — a system info tool with an ASCII cat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            f"Themes: {', '.join(THEMES)}\n"
            f"Styles: {', '.join(CAT_STYLES)}\n"
            f"Fields: {', '.join(FIELD_NAMES)}"
        ),
    )
    p.add_argument(
        "--version", action="version", version=f"mewfetch {VERSION}",
    )
    p.add_argument(
        "--style", default=cfg["style"], choices=list(CAT_STYLES), metavar="STYLE",
        help=f"Cat ASCII art style (default: {cfg['style']})",
    )
    p.add_argument(
        "--theme", default=cfg["theme"], choices=list(THEMES), metavar="THEME",
        help=f"Color theme (default: {cfg['theme']})",
    )
    p.add_argument(
        "--no-color", dest="no_color", action="store_true",
        default=to_bool(cfg.get("no_color", "false")),
        help="Disable colors",
    )
    p.add_argument(
        "--color", dest="no_color", action="store_false",
        help="Enable colors",
    )
    p.add_argument(
        "--no-art", dest="no_art", action="store_true",
        default=to_bool(cfg.get("no_art", "false")),
        help="Disable ASCII art",
    )
    p.add_argument(
        "--art", dest="no_art", action="store_false",
        help="Enable ASCII art",
    )
    p.add_argument(
        "--show-na", dest="show_na", action="store_true",
        default=to_bool(cfg.get("show_na", "false")),
        help="Show fields with N/A values",
    )
    p.add_argument(
        "--hide-na", dest="show_na", action="store_false",
        help="Hide fields with N/A values",
    )
    p.add_argument(
        "--fields", default=cfg.get("fields", ""), metavar="FIELD,...",
        help="Comma-separated list of fields to display (e.g. OS,CPU,RAM)",
    )
    p.add_argument("--json",        action="store_true", help="Output in JSON format")
    p.add_argument("--save-config", action="store_true", help="Save current settings to config file")
    p.add_argument("--list-styles", action="store_true", help="List all available styles")
    p.add_argument("--list-themes", action="store_true", help="List all available themes")
    return p.parse_args()


# ─────────────────────────── Entry Point ──────────────────────────────────────
def main() -> None:
    cfg      = load_config()
    logo_cfg = load_logo_config()
    args     = parse_args(cfg)

    if args.list_styles:
        print("Available cat styles:\n")
        for name, art in CAT_STYLES.items():
            print(f"  [{name}]")
            for line in art:
                print(f"    {line}")
            print()
        return

    if args.list_themes:
        print("Available themes:\n")
        for name, t in THEMES.items():
            print(f"  {t['label']}{name:10}{RESET}  {t['value']}sample text{RESET}")
        return

    if args.save_config:
        save_config(args)
        return

    # Field selection
    fields_str = args.fields or cfg.get("fields", "")
    if fields_str:
        wanted = {f.strip().lower() for f in fields_str.split(",") if f.strip()}
        fields = [(l, f) for l, f in ALL_FIELDS if l.lower() in wanted]
        if not fields:
            print(
                f"No matching fields found. Available: {', '.join(FIELD_NAMES)}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        fields = ALL_FIELDS

    # Concurrent collection
    info = gather_info(fields, show_na=args.show_na)

    # JSON mode
    if args.json:
        print(json.dumps(dict(info), ensure_ascii=False, indent=2))
        return

    # Render
    render(
        style=args.style,
        theme=THEMES.get(args.theme, THEMES["pink"]),
        info=info,
        no_art=args.no_art,
        no_color=args.no_color,
        logo_cfg=logo_cfg,
    )


if __name__ == "__main__":
    main()
