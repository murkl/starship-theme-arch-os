<div align="center">

# Arch OS Starship Theme

![](./screenshot-01.png)

![](./screenshot-02.png)

<details>
<summary><b>Legacy Version</b></summary>

<br>

![](./screenshot-legacy-01.png)

![](./screenshot-legacy-02.png)

</details>

## 1. Install Starship

```bash
sudo pacman -S starship
```

[Configure your shell](https://starship.rs/guide/#step-2-set-up-your-shell-to-use-starship)

## 2. Download Theme

```bash
curl -L https://raw.githubusercontent.com/murkl/starship-theme-arch-os/refs/heads/main/starship.toml > ~/.config/starship.toml
```

<details>
<summary><b>Legacy Version</b></summary>

<br>

```bash
curl -L https://raw.githubusercontent.com/murkl/starship-theme-arch-os/refs/heads/main/starship-legacy.toml > ~/.config/starship.toml
```

</details>

## 3. Copy to Root _(optional)_

```bash
sudo cp -f ~/.config/starship.toml /root/.config/starship.toml
```

> [!CAUTION]
> These commands replace your existing Starship configuration.

<br>

![](https://img.shields.io/badge/MAINTAINED-YES-green?style=for-the-badge)
![](https://img.shields.io/badge/License-GPL_v2-blue?style=for-the-badge)

Used by [Arch OS](https://github.com/murkl/arch-os)

</div>
