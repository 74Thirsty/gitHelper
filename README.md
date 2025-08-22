# GitHub Operations Script
<p align="center">
  <img src="https://i.postimg.cc/hv3TnBYf/profit-cropped.gif">
</p>

<a href="#"><img src="https://img.shields.io/badge/Built%20with-PyCharm-8fbad9?logo=pycharm&logoColor=black&labelColor=7bafd4"></a>
<a href="#"><img src="https://img.shields.io/badge/Python-3.10_|_3.11_|_3.12-b7d0e3?logo=python&logoColor=black&labelColor=a3c5de"></a>
<a href="#"><img src="https://img.shields.io/badge/Solidity-0.8.20_|_0.8.28-dfe7ed?logo=ethereum&logoColor=black&labelColor=cbdce8"></a>
<a href="#"><img src="https://img.shields.io/badge/Flashbots-MEV%20Bundle-b7d0e3?logo=thunderbird&logoColor=black&labelColor=cbdce8"></a>
<a href="#"><img src="https://img.shields.io/badge/Ephemeral-Contracts-7bafd4?logo=nodedotjs&logoColor=black&labelColor=8fbad9"></a>

---


An interactive script for managing Git operations, GitHub Pages deployment, and SSH key management. This script helps automate common Git tasks and integrates with GitHub Pages and GitHub Codespaces. It also provides utilities for generating and managing SSH keys.

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

### SSH Key Management:

* **Generate SSH Key**: Generate a new SSH key pair for use with GitHub.
* **Add SSH Key to Agent**: Add the SSH key to the SSH agent for seamless GitHub authentication.
* **Add SSH Key to GitHub**: Display the public key and prompt you to add it to your GitHub account via the GitHub web interface.

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
