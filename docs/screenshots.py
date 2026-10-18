#!/usr/bin/env python3
"""Renders docs/screenshots/: the short prompt at home and the long one over SSH
in a git repository, each on the card arch-os pictures its interface on. By
hand after a visible change.

Starship runs as tux on arch-os in throwaway namespaces, so nothing of this
machine shows. Needs chromium, imagemagick, git and ttf-firacode-nerd.

  docs/screenshots.py
"""

import html
import itertools
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/screenshots"
README = ROOT / "docs/README.md"

# The card of arch-os/docs/screenshots.py, in the font arch-os sets for GNOME.
FONT = "FiraCode Nerd Font"
FONT_PX, LINE_PX = 15, 22
PAD, RADIUS, SCALE = 26, 10, 2
LEAD = (LINE_PX - FONT_PX) / 2
CARD, TEXT = "#2e3440", "#d8dee9"

# The separator fills its whole cell, as a terminal draws it. From the font it
# would stop short of the line height.
PAINT = {"": "linear-gradient(to bottom right, {fg} 50%, {bg} 50%)"}

# The machine as Starship sees it: its name, one address and the user.
MACHINE = """
hostname arch-os
mount --bind "$PASSWD" /etc/passwd
ip link add eth0 type dummy
ip address add 192.168.1.10/24 dev eth0
ip link set eth0 up
ip route add default dev eth0
exec "$@"
"""

SGR = re.compile(r"\x1b\[([0-9;]*)m")


def prompt(tmp, cwd, shell, *args, **env):
    """One prompt as Starship prints it, without the markers a shell reads."""
    run = subprocess.run(
        ["unshare", "--user", "--map-current-user", "--keep-caps", "--uts", "--net", "--mount",
         "sh", "-ec", MACHINE, "sh", "starship", "prompt", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
        env={"PATH": os.environ["PATH"], "HOME": str(tmp / "home"), "USER": "tux",
             "LOGNAME": "tux", "PASSWD": str(tmp / "passwd"), "STARSHIP_SHELL": shell,
             "STARSHIP_CONFIG": str(ROOT / "starship.toml"), "STARSHIP_CACHE": str(tmp / "cache"),
             **env})
    if run.stderr:
        sys.exit(run.stderr)
    return re.sub(r"\\\[|\\\]|%\{|%\}", "", run.stdout).replace("%%", "%")


def cells(line):
    """(char, fg, bg, bold) for every cell, out of the SGR codes Starship writes."""
    fg = bg = None
    bold = False
    out = []
    for i, part in enumerate(SGR.split(line)):
        if not i % 2:
            if "\x1b" in part:
                sys.exit(f"no rendering for {part!r}")
            out += [(char, fg, bg, bold) for char in part]
            continue
        codes = [int(c) for c in part.split(";") if c] or [0]
        while codes:
            code = codes.pop(0)
            if code == 0:
                fg = bg = None
                bold = False
            elif code == 1:
                bold = True
            elif code in (38, 48) and codes[:1] == [2]:
                color = "#{:02x}{:02x}{:02x}".format(*codes[1:4])
                del codes[:4]
                fg, bg = (color, bg) if code == 38 else (fg, color)
            else:
                sys.exit(f"no rendering for SGR code {code}")
    return out


def markup(row):
    """One span a run of same-looking cells, each exactly one line tall."""
    spans = []
    key = lambda c: (c[1] or TEXT, c[2], c[3], c[0] if c[0] in PAINT else None)
    for (fg, bg, bold, paint), run in itertools.groupby(row, key):
        text = "".join(c[0] for c in run)
        style = f"display:inline-block;vertical-align:top;height:{LINE_PX}px;"
        if paint:
            style += "background:" + PAINT[paint].format(fg=fg, bg=bg or CARD)
            text = " " * len(text)
        else:
            style += f"color:{fg};" + (f"background:{bg};" if bg else "")
            style += "font-weight:700;" if bold else ""
        spans.append(f'<span style="{style}">{html.escape(text)}</span>')
    return "".join(spans)


def card(rows, tmp, out):
    """The rows on a rounded card, the picture trimmed back to the card. Returns
    the width to show it at, in CSS pixels."""
    page = tmp / "card.html"
    page.write_text(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; }}
  body {{ background:transparent; }}
  .card {{
    display:inline-block; padding:{PAD - LEAD}px {PAD}px;
    background:{CARD}; border-radius:{RADIUS}px;
  }}
  pre {{
    font-family:"{FONT}"; font-size:{FONT_PX}px; line-height:{LINE_PX}px;
    color:{TEXT}; white-space:pre; font-variant-ligatures:none;
  }}
</style></head><body><div class="card"><pre>{"\n".join(map(markup, rows))}</pre></div></body></html>""")
    # No glyph advance is wider than the font size, so the card always fits.
    width = max(map(len, rows)) * FONT_PX + 4 * PAD
    height = len(rows) * LINE_PX + 4 * PAD
    subprocess.run([
        "chromium", "--headless", f"--user-data-dir={tmp / 'chromium'}",
        f"--force-device-scale-factor={SCALE}", "--default-background-color=00000000",
        "--hide-scrollbars", f"--window-size={width},{height}", f"--screenshot={out}",
        page.as_uri(),
    ], check=True, capture_output=True)
    subprocess.run(["magick", str(out), "-trim", "+repage", str(out)], check=True)
    # Even on both axes, so half its pixels is a whole width and nothing resamples.
    size = subprocess.run(["magick", "identify", "-format", "%w %h", str(out)],
                          capture_output=True, text=True, check=True).stdout
    w, h = (n + n % 2 for n in map(int, size.split()))
    subprocess.run(["magick", str(out), "-background", "none", "-gravity", "center",
                    "-extent", f"{w}x{h}", "-strip", "-define", "png:compression-level=9",
                    str(out)], check=True)
    print(out.relative_to(ROOT))
    return w // SCALE


def main():
    found = subprocess.run(["fc-match", "-f", "%{family}", FONT],
                           capture_output=True, text=True, check=True).stdout
    if FONT not in found.split(","):
        sys.exit(f"needs {FONT}: sudo pacman -S ttf-firacode-nerd")

    with tempfile.TemporaryDirectory() as name:
        tmp = pathlib.Path(name)
        repo = tmp / "home/Projekte/arch-os"
        repo.mkdir(parents=True)
        (tmp / "passwd").write_text(f"tux:x:{os.getuid()}:{os.getgid()}::/home/tux:/bin/bash\n")

        # A repository with one change, out of reach of this user's git config.
        git = ["git", "-C", str(repo), "-c", "user.name=tux", "-c", "user.email=tux@arch-os"]
        env = os.environ | {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
        (repo / "README.md").write_text("# Arch OS\n")
        for args in (["init", "-q", "-b", "main"], ["add", "."], ["commit", "-q", "-m", "init"]):
            subprocess.run(git + args, env=env, check=True)
        (repo / "README.md").write_text("# Arch OS\n\nInstall Arch Linux with ease.\n")

        ssh = {"SSH_CONNECTION": "192.168.1.2 50022 192.168.1.10 22", "SHLVL": "2"}
        short = prompt(tmp, tmp / "home", "zsh")
        long = prompt(tmp, repo, "bash", **ssh)
        right = prompt(tmp, repo, "bash", "--right", "--cmd-duration=2400", **ssh)

        short, long, right = (list(map(cells, p.split("\n"))) for p in (short, long, right))
        long[0] += [(" ", None, None, False)] * 6 + right[0]

        # The README shows each card at its CSS width, the one place it is set.
        OUT.mkdir(exist_ok=True)
        readme = README.read_text()
        for name, rows in (("short", short), ("long", long)):
            width = card(rows, tmp, OUT / f"{name}.png")
            readme, found = re.subn(rf'(<img src="screenshots/{name}\.png" width=")\d+"',
                                    rf'\g<1>{width}"', readme)
            if found != 1:
                sys.exit(f'docs/README.md: needs one <img src="screenshots/{name}.png" width="…">')
        README.write_text(readme)


if __name__ == "__main__":
    main()
