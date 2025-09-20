# GitHub Operations Script

![GADGET SAAVY banner](https://raw.githubusercontent.com/74Thirsty/74Thirsty/main/assets/banner.svg)


[![Cyfrin](https://img.shields.io/badge/Cyfrin-Audit%20Ready-005030?logo=shield&labelColor=F47321)](https://www.cyfrin.io/)
[![Python](https://img.shields.io/badge/Python-3.11-003057?logo=python&labelColor=B3A369)](https://www.python.org/)
[![pYcHARM](https://img.shields.io/badge/Built%20with-PyCharm-782F40?logo=pycharm&logoColor=CEB888)](https://www.jetbrains.com/pycharm/)
[![Issues](https://img.shields.io/github/issues/74Thirsty/gitHelper.svg?color=hotpink&labelColor=brightgreen)](https://github.com/74Thirsty/gitHelper/issues)
[![Security](https://img.shields.io/badge/encryption-AES--256-orange.svg?color=13B5EA&labelColor=9EA2A2)]()

> <p><strong>Christopher Hirschauer</strong><br>
> Builder @ the bleeding edge of MEV, automation, and high-speed arbitrage.<br>
<em>August 21, 2025</em></p>
---


An interactive script for managing Git operations, GitHub Pages deployment, and SSH key management. This script helps automate common Git tasks and integrates with GitHub Pages and GitHub Codespaces. It also provides utilities for generating and managing SSH keys.

## gitHelper control centre (CLI)

Prefer a guided workflow without leaving the shell? Launch the new **gitHelper control centre** for a colourful, modern command-line experience focused on day-to-day automation tasks:

```bash
python -m git_helper
```

The CLI surfaces the most common actions behind friendly menus and emoji-powered feedback:

* **Repository directory management** – review the active workspace, switch to a different folder, or create it on the fly with automatic validation and recovery when paths are invalid.
* **Repository overview** – quickly list all Git repositories that live under the configured workspace.
* **Git repository workflow** – select or initialise projects, stage files, craft commits, and push/pull with upstream tracking prompts.
* **SSH key concierge** – generate fresh Ed25519 keys, import existing keys into `~/.ssh`, and optionally register them with the local `ssh-agent`, all with detailed success and error messaging.

The interface is implemented as a first-class Python package (`git_helper`) making it easy to install with `pip`, script against, or extend. Rich inline documentation and modular components keep future maintenance approachable.

> Pro tip: type `?` or `help` on any screen to open a contextual help panel summarising available shortcuts and actions.

## Neon Git Cockpit (Terminal UI)

Prefer a neon-lit command center instead of memorising dozens of git commands? Launch the curses-powered **neon git cockpit** and cruise through commits, branches, GitHub issues, and dangerous operations without leaving the terminal.

```text
┌─────────────────────────────── NEON GIT COCKPIT ───────────────────────────────┐
│ HEAD: main | Theme: github_dark | View: diff                                   │
├─────────────────────────┬──────────────────────────────────────────────────────┤
│ Timeline                │ Diff / GitHub / Danger Zone Panel                   │
│ ➤ 9f31b1 2025-08-20 ch  │ commit 9f31b1 (Chris)                               │
│   41a62a 2025-08-19 fea │ + Add neon cockpit + GitHub sync panel              │
│   3d9c72 2025-08-18 fix │ - Remove brittle shell prompts                      │
├─────────────────────────┴──────────────────────────────────────────────────────┤
│ Status: press ? for hotkeys           Undo:1  Redo:0  GitHub: issues ▷ pulls   │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Cockpit superpowers

* **Repo browser** – scroll commits with ↑/↓, press `Enter` for rich diffs, `Space` to pop into a temporary branch.
* **Branch playground** – jump to the branch graph, fast-forward with `F`, or merge after previewing diff stats.
* **GitHub sync** – hit `G` for live lists of issues, pull requests, and Actions runs (powered by the `gh` CLI). Type `#42` in search to grab a specific PR instantly.
* **Danger zone** – slam `D` to reveal rollback, skull-certified force push, and stashing prompts (with built-in safety nets).
* **Interactive rebase** – `R` launches a GUI-like checklist. Use `p/s/f/e/r/x` to mark actions before executing.
* **Plug-ins** – press `P` for extensibility. A sample “ML-ish commit oracle” plugin analyses your diff and proposes cheeky messages.
* **Themes & vibes** – configuration lives at `~/.config/neon_git/config.json` with presets for GitHub Dark, Matrix Green, and Neon Cyberpunk.

### Quickstart

```bash
python3 neogit.py
```

```bash
python -m git_helper
```

Key hotkeys are always a `?` away:

| Key | Action |
| --- | --- |
| `↑/↓` | Navigate commits |
| `Space` | Checkout selected commit in a temporary branch |
| `Tab` | Create a new branch from the highlighted commit |
| `F` | Fast-forward to the tracked main branch |
| `G` | Open GitHub panel (requires [`gh`](https://cli.github.com/)) |
| `R` | Launch interactive rebase planner |
| `P` | Browse and run plug-ins |
| `D` | Toggle the danger zone overlay |
| `/` | Search commits or jump to `#<issue>`/`#<PR>` |
| `U` / `Shift+U` | Undo / redo git state snapshots |
| `Q` | Quit the cockpit |

> **GitHub integration:** the cockpit auto-detects your `origin` remote. Make sure `gh auth login` has been run and the CLI is in PATH.

### Plug-in architecture

Drop Python modules inside `neogit_tui/plugins/` that expose a `register()` function returning a `Plugin`. Each plug-in receives the active `GitInterface` instance, so you can build bots for semantic PR labels, AI commit messages, or workflow dashboards.

```python
from neogit_tui.git import GitInterface
from neogit_tui.plugins import Plugin


def register() -> Plugin:
    def run(git: GitInterface, app) -> str:
        summary = git.diff_stat()
        return f"Diff summary\n{summary}"

    return Plugin(
        name="Diff Summariser",
        description="Show a quick diffstat report",
        run=run,
    )
```

Restart the cockpit and your plug-in appears instantly in the `P` menu.

## Features

### Classic Bash Helper

If you prefer the original guided prompts, the `ghHelper.sh` script is still included.

### General Git Operations:

* **Clone a Repository**: Clone any GitHub repository to your local machine.
* **Create & Checkout Branches**: Create a new branch or switch between existing branches.
* **Add, Commit & Push Changes**: Stage changes with `git add .`, commit changes, and push them to the remote repository.
* **Force Push Changes**: Force push changes to the remote repository (overwrites existing history).
* **View Commit History**: View the commit log in a simplified format.
* **Revert to a Previous Commit**: Revert the repository to a specific commit.
* **Pull Latest Updates**: Fetch and merge updates from the remote repository.

### GitHub Pages and Codespaces:

* **Deploy to GitHub Pages**: Deploy changes to a `gh-pages` branch or main branch, for GitHub Pages hosting.
* **Open a GitHub Codespace**: Create and open a GitHub Codespace for your repository.

### Repository Directory Management:

* **Change workspace location**: Point gitHelper at any directory, create it automatically, and persist the choice across sessions.
* **Validate paths**: Friendly error handling highlights invalid or inaccessible paths before they cause issues.
* **Repository overview**: List all detected Git repositories living inside the configured workspace.

### SSH Key Management:

* **Generate SSH Key**: Generate a new Ed25519 SSH key pair with optional passphrase and overwrite protection.
* **Import SSH Key**: Copy existing keys into `~/.ssh`, preserve the matching public key, and optionally register them with `ssh-agent`.
* **Add SSH Key to Agent**: Add any key to the SSH agent for seamless GitHub authentication with detailed success/error feedback.

## Prerequisites

Before using this script, ensure that the following tools are installed on your system:

* **Pluma** (for editing `README.md`):
  Install with:

  ```bash
  sudo apt install pluma
  ```

* **GitHub CLI (`gh`)** (for GitHub Codespaces integration):
  Install with:

  ```bash
  sudo apt install gh
  ```

## Installation

1. Download or clone this repository:

   ```bash
   git clone https://github.com/username/repo.git
   ```

2. Make the script executable:

   ```bash
   chmod +x github_operations.sh
   ```

3. Run the script:

   ```bash
   ./github_operations.sh
   ```

## Usage

### Main Menu Options:

* **Create a new branch**: Create a new Git branch for feature development or bug fixes.
* **Checkout an existing branch**: Switch between branches within the repository.
* **Add changes**: Stage changes (`git add .`).
* **Commit changes**: Commit your staged changes with a commit message.
* **Push changes**: Push your local commits to the remote repository.
* **Force push**: Force push your changes to overwrite the remote history.
* **Show all commits**: View the commit history.
* **Revert to a previous commit**: Roll back the repository to a specific commit.
* **Pull updates**: Fetch and merge the latest changes from the remote repository.
* **Update `README.md`**: Open `README.md` for editing with Pluma. Commit and push changes to GitHub.

### GitHub Pages and Codespaces:

* **Deploy to GitHub Pages**: Deploy your site to GitHub Pages using the `gh-pages` branch.
* **Open GitHub Codespace**: Create and open a GitHub Codespace for cloud-based development.

### SSH Key Operations:

* **Generate a new SSH key**: Generate a new SSH key pair for GitHub authentication.
* **Add SSH key to the agent**: Add your SSH private key to the SSH agent for use with GitHub.
* **Add SSH key to GitHub**: Display your public SSH key and guide you to add it to GitHub.

### Example Workflow

1. **Clone a repository**:

   ```bash
   Enter the GitHub repository URL (e.g., https://github.com/username/repo.git): https://github.com/username/repo.git
   ```

2. **Create a new branch**:

   ```bash
   Enter the new branch name: feature-xyz
   ```

3. **Add and commit changes**:

   ```bash
   Do you want to add all changes? (y/n): y
   Enter commit message: Added new feature XYZ
   ```

4. **Push changes to GitHub**:

   ```bash
   Do you want to push changes to the repository? (y/n): y
   ```

5. **Deploy to GitHub Pages**:

   ```bash
   Deploying to GitHub Pages...
   ```

6. **Generate an SSH Key**:

   ```bash
   Enter your email address (for SSH key): youremail@example.com
   ```

7. **Add SSH Key to GitHub**:

   ```bash
   Copy the SSH key and add it to GitHub under 'Settings' -> 'SSH and GPG keys'.
   ```

## Script Overview

The script is divided into different operation categories to help manage GitHub repositories, GitHub Pages, and SSH key management. It provides a menu-driven interface where users can perform the following tasks:

* Manage Git branches, commits, and pushes.
* Deploy content to GitHub Pages for static site hosting.
* Create and manage SSH keys for secure GitHub authentication.
* Launch a GitHub Codespace for cloud development.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
