#!/bin/bash

# GitHub Operations Script
# This script allows users to interactively perform basic GitHub tasks.

echo "Welcome to the Interactive GitHub Operations Script!"

# Ask for the repository URL or initialize a new repo if no URL is provided
read -p "Enter the GitHub repository URL (e.g., https://github.com/username/repo.git) or leave empty to initialize a new repo: " repo_url

# If repo_url is empty, initialize a new repository
if [ -z "$repo_url" ]; then
    echo "Initializing a new Git repository..."
    git init || { echo "Failed to initialize repository. Exiting."; exit 1; }
    echo "New Git repository initialized."
else
    # Clone the repository if a URL is provided
    echo "Cloning repository from $repo_url..."
    git clone "$repo_url" || { echo "Failed to clone repository. Exiting."; exit 1; }

    # Change into the repository directory
    repo_name=$(basename "$repo_url" .git)
    cd "$repo_name" || { echo "Failed to navigate into the repository directory. Exiting."; exit 1; }
fi

# Display the main menu of options
while true; do
    echo "Choose an operation:"
    echo "1. Create a new branch"
    echo "2. Checkout an existing branch"
    echo "3. Add changes (git add .)"
    echo "4. Commit changes"
    echo "5. Push changes"
    echo "6. Force push to remote"
    echo "7. Show all commits"
    echo "8. Revert to a previous commit"
    echo "9. Pull updates from the remote repository"
    echo "10. Update README.md (Open with Pluma)"
    echo "11. GitHub Pages and Codespaces Operations"
    echo "12. SSH Key Operations"
    echo "13. Exit"

    read -p "Enter your choice (1-13): " choice

    case $choice in
        1)  # Create a new branch
            read -p "Enter the new branch name: " branch_name
            git checkout -b "$branch_name" || { echo "Failed to create or switch to branch. Exiting."; exit 1; }
            echo "Switched to new branch: $branch_name"
            ;;
        2)  # Checkout an existing branch
            read -p "Enter the branch name you want to checkout: " branch_name
            git checkout "$branch_name" || { echo "Failed to checkout branch. Exiting."; exit 1; }
            echo "Switched to branch: $branch_name"
            ;;
        3)  # Add changes (git add .)
            echo "Now, let's stage your changes. This will add all changes in the repository."
            git add . || { echo "Failed to add changes. Exiting."; exit 1; }
            echo "All changes added."
            ;;
        4)  # Commit changes
            read -p "Enter commit message: " commit_message
            git commit -m "$commit_message" || { echo "Failed to commit changes. Exiting."; exit 1; }
            echo "Changes committed with message: $commit_message"
            ;;
        5)  # Push changes
            read -p "Do you want to push changes to the repository? (y/n): " push_changes
            if [[ "$push_changes" == "y" || "$push_changes" == "Y" ]]; then
                git push origin "$branch_name" || { echo "Failed to push changes. Exiting."; exit 1; }
                echo "Changes pushed to $branch_name."
            fi
            ;;
        6)  # Force push changes
            read -p "Are you sure you want to force push to the repository? This will overwrite remote changes! (y/n): " force_push
            if [[ "$force_push" == "y" || "$force_push" == "Y" ]]; then
                git push --force origin "$branch_name" || { echo "Failed to force push changes. Exiting."; exit 1; }
                echo "Force pushed changes to $branch_name."
            fi
            ;;
        7)  # Show all commits
            git log --oneline || { echo "Failed to show commits. Exiting."; exit 1; }
            ;;
        8)  # Revert to a previous commit
            read -p "Enter the commit hash to revert to: " commit_hash
            git checkout "$commit_hash" || { echo "Failed to revert to commit. Exiting."; exit 1; }
            echo "Reverted to commit $commit_hash."
            ;;
        9)  # Pull updates from the remote repository
            read -p "Do you want to pull the latest updates from the remote repository? (y/n): " pull_updates
            if [[ "$pull_updates" == "y" || "$pull_updates" == "Y" ]]; then
                git pull origin "$branch_name" || { echo "Failed to pull updates. Exiting."; exit 1; }
                echo "Pulled latest updates from remote."
            fi
            ;;
        10)  # Update README.md (Open with Pluma)
            if [[ -f "README.md" ]]; then
                echo "Opening README.md with Pluma..."
                pluma README.md || { echo "Failed to open README.md with Pluma. Ensure Pluma is installed. Exiting."; exit 1; }
                read -p "Do you want to commit and push the changes to README.md? (y/n): " commit_readme
                if [[ "$commit_readme" == "y" || "$commit_readme" == "Y" ]]; then
                    git add README.md || { echo "Failed to add README.md. Exiting."; exit 1; }
                    read -p "Enter commit message for README.md: " commit_message
                    git commit -m "$commit_message" || { echo "Failed to commit changes to README.md. Exiting."; exit 1; }
                    git push origin "$branch_name" || { echo "Failed to push changes to README.md. Exiting."; exit 1; }
                    echo "README.md changes committed and pushed."
                fi
            else
                echo "README.md file not found in this repository."
            fi
            ;;
        11)  # GitHub Pages and Codespaces Operations Menu
            while true; do
                echo "GitHub Pages and Codespaces Operations:"
                echo "1. Deploy to GitHub Pages"
                echo "2. Open a GitHub Codespace"
                echo "3. Back to Main Menu"

                read -p "Enter your choice (1-3): " gh_choice

                case $gh_choice in
                    1)  # Deploy to GitHub Pages
                        echo "Deploying to GitHub Pages..."
                        # Assume the user has a `gh-pages` branch or deploys to main automatically
                        git checkout gh-pages || git checkout main
                        # You can modify this to automate the build process
                        git add . || { echo "Failed to add files for Pages deployment. Exiting."; exit 1; }
                        read -p "Enter commit message for Pages deployment: " pages_commit_msg
                        git commit -m "$pages_commit_msg" || { echo "Failed to commit changes. Exiting."; exit 1; }
                        git push origin gh-pages || { echo "Failed to push to GitHub Pages. Exiting."; exit 1; }
                        echo "Deployed to GitHub Pages successfully."
                        ;;
                    2)  # Open a GitHub Codespace
                        echo "Opening GitHub Codespace..."
                        # Assume that the user has a GitHub account linked and is using the CLI
                        gh codespace create --repo "$repo_url" --branch "$branch_name" || { echo "Failed to create Codespace. Exiting."; exit 1; }
                        echo "Codespace created successfully."
                        ;;
                    3)  # Back to the main menu
                        break
                        ;;
                    *)  # Invalid GitHub Pages/Codespaces option
                        echo "Invalid choice, please enter a number between 1 and 3."
                        ;;
                esac
            done
            ;;
        12)  # SSH Key Operations Menu
            while true; do
                echo "SSH Key Operations:"
                echo "1. Generate a new SSH key"
                echo "2. Add SSH key to the SSH agent"
                echo "3. Add SSH key to GitHub"
                echo "4. Back to Main Menu"

                read -p "Enter your choice (1-4): " ssh_choice

                case $ssh_choice in
                    1)  # Generate a new SSH key
                        echo "Generating a new SSH key..."
                        read -p "Enter your email address (for SSH key): " email
                        ssh-keygen -t rsa -b 4096 -C "$email" || { echo "Failed to generate SSH key. Exiting."; exit 1; }
                        echo "SSH key generated successfully."
                        ;;
                    2)  # Add SSH key to the SSH agent
                        echo "Adding SSH key to the SSH agent..."
                        eval "$(ssh-agent -s)" || { echo "Failed to start SSH agent. Exiting."; exit 1; }
                        read -p "Enter the path to your SSH private key (default: ~/.ssh/id_rsa): " ssh_key_path
                        ssh-add "${ssh_key_path:-~/.ssh/id_rsa}" || { echo "Failed to add SSH key to agent. Exiting."; exit 1; }
                        echo "SSH key added to the SSH agent."
                        ;;
                    3)  # Add SSH key to GitHub
                        echo "Adding SSH key to GitHub..."
                        cat ~/.ssh/id_rsa.pub || { echo "Failed to display SSH public key. Exiting."; exit 1; }
                        read -p "Copy the SSH key and add it to GitHub under 'Settings' -> 'SSH and GPG keys'. Press Enter when done: "
                        echo "SSH key added to GitHub."
                        ;;
                    4)  # Back to the main menu
                        break
                        ;;
                    *)  # Invalid SSH Key option
                        echo "Invalid choice, please enter a number between 1 and 4."
                        ;;
                esac
            done
            ;;
        13)  # Exit the script
            echo "Exiting GitHub Operations Script."
            exit 0
            ;;
        *)  # Invalid option
            echo "Invalid choice, please enter a number between 1 and 13."
            ;;
    esac
done
