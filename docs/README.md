<div align="center">

<p><img src="banner.png" alt="Arch OS Starship Theme: the prompt at home, and over SSH in a git repository"></p>

<p>A clean <b>Nord</b> prompt that shows only what matters right now.</p>

<p>
  <a href="https://github.com/murkl/arch-os"><img src="https://img.shields.io/static/v1?label=made%20for&message=Arch%20OS&color=5e81ac&style=flat-square" alt="Made for Arch OS"></a>
  <a href="https://starship.rs"><img src="https://img.shields.io/static/v1?label=theme%20for&message=Starship&color=5e81ac&style=flat-square" alt="Theme for Starship"></a>
  <a href="../LICENSE"><img src="https://img.shields.io/github/license/murkl/starship-theme-arch-os?style=flat-square&color=5e81ac" alt="License"></a>
</p>

</div>

## Features

Each part appears only when it applies:

- Host and address over SSH
- User over SSH or as root
- Shell other than zsh, nesting level
- Git branch and status, package version, Docker context
- Read-only directories marked
- Duration of commands over half a second
- Red prompt after an error

## Installation

```sh
sudo pacman -S starship ttf-firacode-nerd
```

Set **FiraCode Nerd Font** as the terminal font, [set up your shell](https://starship.rs/guide/#step-2-set-up-your-shell-to-use-starship), then fetch the theme. The same command updates it later:

```sh
curl --proto '=https' -fsSL --create-dirs -o ~/.config/starship.toml https://raw.githubusercontent.com/murkl/starship-theme-arch-os/main/starship.toml
```

> [!CAUTION]
> This overwrites an existing `~/.config/starship.toml`. Back it up first to keep it.
