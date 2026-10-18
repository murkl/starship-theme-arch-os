#!/usr/bin/env python3
"""Renders docs/banner.png: the name over the short prompt at home and the long
one over SSH in a git repository, by hand after a visible change.

Starship runs as tux on arch-os in throwaway namespaces, so nothing of this
machine shows. Needs chromium, imagemagick, git and ttf-firacode-nerd.

  docs/banner.py
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
OUT = ROOT / "docs/banner.png"

# The card of arch-os/docs/screenshots.py, in the font arch-os sets for GNOME.
FONT = "FiraCode Nerd Font"
FONT_PX, LINE_PX = 15, 22
PAD, RADIUS, SCALE = 26, 10, 2
LEAD = (LINE_PX - FONT_PX) / 2
CARD, TEXT = "#2e3440", "#d8dee9"

# Nord frost, light under the name, where its ink keeps 6:1, deeper under the
# cards. Both ends stand off a light page and a dark one.
BAND = "linear-gradient(120deg, #88c0d0, #5e81ac)"
INK = "#2e3440"

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


def card(rows):
    return f'<div class="card"><pre>{"\n".join(map(markup, rows))}</pre></div>'


def banner(short, long, tmp):
    """The name over both cards on one band, the picture trimmed back to the band."""
    page = tmp / "banner.html"
    page.write_text(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; }}
  body {{ background:transparent; font-family:"{FONT}"; }}
  .band {{
    display:inline-flex; flex-direction:column; gap:{PAD}px; padding:{2 * PAD}px;
    background:{BAND}; border-radius:{2 * RADIUS}px; color:{INK};
  }}
  .eyebrow {{ font-size:16px; letter-spacing:.4em; }}
  .name {{ font-size:40px; font-weight:700; line-height:1.2; }}
  .cards {{ display:flex; gap:{PAD}px; }}
  .card {{
    padding:{PAD - LEAD}px {PAD}px; background:{CARD}; border-radius:{RADIUS}px;
    box-shadow:0 12px 32px rgb(46 52 64 / 35%);
  }}
  pre {{
    font-family:inherit; font-size:{FONT_PX}px; line-height:{LINE_PX}px;
    color:{TEXT}; white-space:pre; font-variant-ligatures:none;
  }}
</style></head><body><div class="band">
  <div><div class="eyebrow">ARCH OS</div><div class="name">Starship Theme</div></div>
  <div class="cards">{card(short)}{card(long)}</div>
</div></body></html>""")
    # No glyph advance is wider than the font size, so the band always fits.
    width = (len(short[0]) + len(long[0])) * FONT_PX + 12 * PAD
    height = (len(long) + 6) * LINE_PX + 8 * PAD
    subprocess.run([
        "chromium", "--headless", f"--user-data-dir={tmp / 'chromium'}",
        f"--force-device-scale-factor={SCALE}", "--default-background-color=00000000",
        "--hide-scrollbars", f"--window-size={width},{height}", f"--screenshot={OUT}",
        page.as_uri(),
    ], check=True, capture_output=True)
    subprocess.run(["magick", str(OUT), "-trim", "+repage", "-strip",
                    "-define", "png:compression-level=9", str(OUT)], check=True)
    print(OUT.relative_to(ROOT))


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
        long[0] += [(" ", None, None, False)] * 4 + right[0]
        banner(short, long, tmp)


if __name__ == "__main__":
    main()
