# GitHub Operations Script

This script allows you to interactively perform common Git operations. It includes a variety of options for managing repositories, branches, commits, deployments to GitHub Pages, and integration with GitHub Codespaces. The operations are accessible through an easy-to-use text-based menu.

## Features:

1. **Clone a Repository**
   Clone any GitHub repository to your local machine.

2. **Create and Checkout Branches**
   Create new branches or switch between existing ones.

3. **Stage and Commit Changes**
   Add changes to the staging area and commit them with a message.

4. **Push and Force Push Changes**
   Push your local changes to the remote repository. The script also allows for forced pushes, which will overwrite remote changes.

5. **View Commit History**
   Show all commits made on the current branch.

6. **Revert to a Previous Commit**
   Revert to a specific commit using its hash.

7. **Pull Latest Updates**
   Pull the latest changes from the remote repository.

8. **Update `README.md`**
   Open `README.md` for editing in the Pluma text editor. After editing, you can commit and push the changes to the repository.

9. **GitHub Pages and Codespaces Operations**

   * **Deploy to GitHub Pages**: Deploy the current repository to GitHub Pages.
   * **Open GitHub Codespace**: Create and open a new GitHub Codespace for the current repository and branch.

10. **Exit**
    Exit the script.

## Requirements:

* **Pluma**: Used to edit the `README.md` file. Install it using:

  ```bash
  sudo apt install pluma
  ```
* **GitHub CLI (`gh`)**: Required for GitHub Codespaces integration. Install it using:

  ```bash
  sudo apt install gh
  ```

## Usage:

1. Save the script as `github_operations.sh`.
2. Make the script executable:

   ```bash
   chmod +x github_operations.sh
   ```
3. Run the script:

   ```bash
   ./github_operations.sh
   ```

Once executed, the script will display an interactive menu with options. Follow the prompts to perform the desired Git operations.

## Example of Workflow:

1. Clone a repository:

   ```bash
   Enter the GitHub repository URL (e.g., https://github.com/username/repo.git): https://github.com/username/repo.git
   ```
2. Create a new branch:

   ```bash
   Enter the new branch name: feature-xyz
   ```
3. Commit changes:

   ```bash
   Enter commit message: Added new feature XYZ
   ```
4. Push changes to the repository:

   ```bash
   Do you want to push changes to the repository? (y/n): y
   ```
5. Deploy to GitHub Pages:

   ```bash
   Deploying to GitHub Pages...
   ```

## Script Overview:

The script guides you through multiple Git operations. Here are the steps:

1. Clone the repository using the repository URL.
2. Navigate to the repository directory.
3. Display an interactive menu with various Git operations.
4. Based on your choices, the script will execute the appropriate Git commands and provide feedback.
5. The script also offers GitHub Pages deployment and Codespaces management, providing a seamless experience for GitHub-based workflows.

## License:

This script is licensed under the MIT License. See LICENSE for more details.

---

This `README.md` provides an overview of the script’s purpose, installation instructions, and examples of usage. Let me know if you need any additional modifications or specific changes!
