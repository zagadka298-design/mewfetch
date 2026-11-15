<div align="center">

<h1>🐱 MewFetch</h1>

<p><em>A lightweight system information tool with cat ASCII art</em></p>

![screenshot](screenshot.png)

<br/>

[![AUR](https://img.shields.io/aur/version/mewfetch?color=1793d1&logo=arch-linux&label=AUR)](https://aur.archlinux.org/packages/mewfetch)
[![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey?logo=linux)](https://kernel.org/)

</div>

---

**MewFetch** is a minimalist alternative to `neofetch` and `fastfetch` written in pure Python 3.  
Zero external dependencies. Just a cat and your system. 🐾

---

## ✨ Features

- **Zero dependencies** — uses only the Python standard library and `/proc`
- **Parallel data fetching** — all fields are gathered concurrently using `threading`
- **19 information fields** — including GPU, disk, battery, packages, IP, and theme
- **6 color themes** — pink, blue, green, red, cyan, mono
- **4 cat ASCII art styles** — classic, small, sleeping, box
- **Full-featured CLI** — `--style`, `--theme`, `--fields`, `--json`, and more
- **Config file** — save preferences in `~/.config/mewfetch/config`
- **Custom logo** — ASCII art or PNG/JPG via `~/.config/mewfetch/config.json`
- **Wayland and X11 support** — resolution detection via `hyprctl` or `xrandr`
- **JSON output** — ready for scripting and piping

---

## 📊 Displayed Information

| Field | Source |
|-------|--------|
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
| **WM** | environment variables / process list |
| **DE** | `XDG_CURRENT_DESKTOP` |
| **Terminal** | `$TERM_PROGRAM`, `$TERM`, `/proc` |
| **Shell** | `$SHELL` |
| **Packages** | pacman / dpkg / rpm / flatpak / snap |
| **Battery** | `/sys/class/power_supply` |
| **IP** | `socket` / `hostname -I` |
| **Theme** | `gsettings` / `gtk-3.0/settings.ini` |
| **Font** | `gsettings` / Hyprland config |

---

## 📦 Installation

### From Source (Any distribution)

```bash
git clone https://github.com/zagadka298-design/mewfetch.git
cd mewfetch
pip install .
```

After installation, the `mewfetch` command will be available globally.

### Running without installation

```bash
git clone https://github.com/zagadka298-design/mewfetch.git
cd mewfetch
python3 -m mewfetch
```

### From AUR (Arch Linux)

> [!WARNING]
> The AUR package has not been updated to v2.1.0 yet — please use the source installation above.

```bash
yay -S mewfetch
# or
paru -S mewfetch
```

---

## 🚀 Usage

```bash
# Basic run
mewfetch

# Choose cat style
mewfetch --style sleeping

# Choose color theme
mewfetch --theme blue

# Display only specific fields
mewfetch --fields OS,CPU,RAM,GPU,Disk

# Disable colors (useful for pipes/scripts)
mewfetch --no-color

# Hide ASCII art
mewfetch --no-art

# JSON output
mewfetch --json

# Save settings
mewfetch --style sleeping --theme cyan --save-config

# List all styles
mewfetch --list-styles

# List all themes
mewfetch --list-themes
```

---

## ⚙️ Configuration File

Settings are stored in `~/.config/mewfetch/config` (created automatically on first launch):

```ini
# mewfetch config
style    = classic
theme    = pink
# fields = OS, CPU, RAM, GPU
show_na  = false
no_color = false
no_art   = false
```

Quickly save configuration via CLI:
```bash
mewfetch --style sleeping --theme cyan --save-config
```

---

## 🖼️ Custom Logo (config.json)

In addition to the main config, mewfetch reads `~/.config/mewfetch/config.json` to configure the logo or image displayed alongside the system info.

The file is generated automatically on first run:

```json
{
  "logo_path": "",
  "logo_type": "ascii"
}
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `logo_path` | string | `""` | Path to the logo file. Empty string → default cat. Supports `~` and environment variables. |
| `logo_type` | string | `"ascii"` | File type: `"ascii"` for text art, `"image"` for PNG/JPG. |

### Example 1: ASCII art from a file

1. Create a file containing your art, for example `~/.config/mewfetch/mycat.txt`:
   ```
      /\_____/\
     /  ^   ^  \
    ( ==  v  == )
     )   mew   (
    (__(_____)__)
   ```

2. Specify the path in `~/.config/mewfetch/config.json`:
   ```json
   {
     "logo_path": "~/.config/mewfetch/mycat.txt",
     "logo_type": "ascii"
   }
   ```

### Example 2: PNG/JPG image

```json
{
  "logo_path": "~/Pictures/mylogo.png",
  "logo_type": "image"
}
```

> [!IMPORTANT]
> The **term-image** library is used to render PNG/JPG images in the terminal.
> Install it:
> ```bash
> pip install term-image
> # or on Arch Linux via pacman:
> sudo pacman -S python-term-image
> ```

> [!NOTE]
> If `term-image` is not installed or the file specified in `logo_path` is not found, mewfetch will print a warning to stderr and fall back to the default ASCII cat.

---

## 🎨 Themes and Styles

### Themes (`--theme`)
| Theme | Accent |
|-------|--------|
| `pink` | Pink (default) |
| `blue` | Blue |
| `green` | Green |
| `red` | Red |
| `cyan` | Cyan |
| `mono` | Monochrome |

### Cat Styles (`--style`)
| Style | Description |
|-------|-------------|
| `classic` | Three cats in one (default) |
| `small` | Small and compact |
| `sleeping` | Sleeping kitty |
| `box` | In a frame |

---

## 🔧 Dependencies

| Dependency | Required | Purpose |
|------------|:--------:|---------| 
| **Python 3.10+** | ✅ | Runtime interpreter |
| `lspci` | ⬜ | GPU detection |
| `hyprctl` | ⬜ | Screen resolution on Hyprland |
| `xrandr` | ⬜ | Screen resolution on X11 |
| `gsettings` | ⬜ | GTK theme and font |
| `term-image` | ⬜ | PNG/JPG logo rendering (`pip install term-image`) |

> All core metrics are read directly from `/proc` and `/etc` — no extra packages required.

---

## 🖥️ Compatibility

| Distribution | Status |
|--------------|:------:|
| EndeavourOS | ✅ |
| Arch Linux | ✅ |
| Manjaro | ✅ |
| Ubuntu / Debian | ✅ |
| Fedora / openSUSE | ✅ |
| Other Linux | ✅ |
| macOS / Windows | ❌ |

**WM/Compositor:**  
Hyprland · Sway · i3 · bspwm · Openbox · dwm · xmonad · Awesome · Fluxbox · KWin · Mutter · XFWM4 · Wayfire · River · Niri · labwc

---

## 📄 License

Distributed under the [MIT](LICENSE) License.  
Do whatever you want, just keep the copyright notice. 🐱

---

<div align="center">
  <sub>Made with ♡ and way too much coffee</sub>
</div>
