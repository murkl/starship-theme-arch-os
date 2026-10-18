#!/usr/bin/env python3
"""Checks starship.toml with Starship, then what Starship lets pass in silence:
a module or palette color that does not exist renders as nothing. Tested
against Starship 1.27.

  ./check.py
"""

import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tomllib

THEME = pathlib.Path(__file__).resolve().parent / "starship.toml"


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def problems(path, modules, cache):
    # Starship names a broken file, an unknown key and a wrong type, and still exits 0.
    env = os.environ | {"STARSHIP_CONFIG": str(path), "STARSHIP_LOG": "warn", "STARSHIP_CACHE": cache}
    run = subprocess.run(["starship", "print-config"], env=env, capture_output=True, text=True, check=True)
    if run.stderr:
        yield run.stderr.strip()
        return

    config = tomllib.loads(path.read_text())
    palette = config.pop("palettes")[config["palette"]]
    used = set(re.findall(r"\$(\w+)", config["format"] + config.get("right_format", "")))
    tables = {key for key, value in config.items() if isinstance(value, dict)}
    colors = {name for text in strings(config) for name in re.findall(r"\bcolor_\w+", text)}

    for what, names in (
        ("unknown module", used - modules),
        ("module not in the format", tables - used),
        ("color not in the palette", colors - palette.keys()),
        ("palette color never used", palette.keys() - colors),
    ):
        if names:
            yield f"{what}: {', '.join(sorted(names))}"


def main():
    listed = subprocess.run(["starship", "module", "--list"], capture_output=True, text=True, check=True)
    modules = {line for line in listed.stdout.splitlines() if re.fullmatch(r"[a-z_]+", line)}
    if not modules:
        sys.exit("starship listed no modules")

    with tempfile.TemporaryDirectory() as cache:
        found = list(problems(THEME, modules, cache))
    for problem in found:
        print(problem, file=sys.stderr)
    if found:
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
