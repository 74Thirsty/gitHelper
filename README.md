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
python -m git_helper
```

Launch the graphical workspace with:

```bash
git-helper --gui
```

The GUI opens directly in your current repository, providing the commit dashboard, plug-in hub, SSH key manager, diagnostics console, the new diff analyzer, and the runtime tracer views without needing any terminal hotkeys.

### Plug-in architecture

Drop Python modules inside `git_helper/plugins/` (or point the settings manager at an additional directory) that expose a `register()` function returning a `Plugin`. Each plug-in receives the active Git interface, so you can build bots for semantic PR labels, AI commit messages, or workflow dashboards.

```python
from git_helper.git_core import GitCore
from git_helper.plugins.base import Plugin


def register(git: GitCore | None = None) -> Plugin:
    def run(git_core: GitCore, app) -> str:
        diff = git_core.run_custom(["diff", "--stat"]).stdout
        return f"Diff summary\n{diff or 'No staged changes.'}"

    return Plugin(
        name="Diff Summariser",
        description="Show a quick diffstat report",
        run=run,
    )
```

Restart the GUI and your plug-in appears instantly in the Plug-in Centre panel.

## Features

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

Before you get started make sure you have:

* **Python 3.9+** – the toolkit is developed and tested with modern Python releases.
* **pip** – for installing the package dependencies.
* **Git** – required for repository operations and for cloning this project.
* **GitHub CLI (`gh`)** – optional, but enables the GitHub integrations exposed by the Neon Git Cockpit and several plug-ins.

> macOS and most Linux distros already ship with Python and Git. On Windows we recommend installing [Python](https://www.python.org/downloads/) and [Git for Windows](https://git-scm.com/download/win). The GitHub CLI can be installed from the [official instructions](https://cli.github.com/manual/installation).

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/74Thirsty/gitHelper.git
   cd gitHelper
   ```

2. **(Optional) Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install the package and dependencies**

   Use the editable install for development or contributions:

   ```bash
   pip install -e .
   ```

   Alternatively you can install from the provided requirements file:

   ```bash
   pip install -r requirements.txt
   ```

4. **Verify the installation**

   ```bash
   python -m git_helper --help
   ```

   This prints the CLI usage banner confirming the package imports correctly.

## Usage

### Launch the gitHelper control centre (CLI)

The control centre provides a guided command palette focused on everyday automation tasks:

```bash
python -m git_helper
```

Select a command from the fuzzy-search palette or press `?` to review the available shortcuts. Configuration such as the default workspace directory is stored under `~/.config/git_helper/config.json`.

### Launch the gitHelper GUI

Prefer visuals? Fire up the KivyMD-powered desktop app for repository dashboards, plug-in management, diff analysis, and the new runtime tracer:

```bash
git-helper --gui
```

Pass `--theme neon_dark` for a neon-accented dark theme. The GUI automatically adopts the current repository and mirrors all plug-in functionality from the CLI.

The script handles repository housekeeping, committing, and pushing without needing to remember command syntax.

### Running unit tests

If you are contributing changes, execute the test suite before opening a pull request:

```bash
pytest
```

This ensures the automation helpers remain stable across Python versions and environments.
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
