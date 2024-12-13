#!/bin/zsh
#
# Script Name: install.sh
# Description: Dotfiles setup script
# Author: $(git config user.name)
# Date Created: 2024-12-08
# Last Modified: 2024-12-08
#
# Usage: install.sh [options]
# Options:
#   -h, --help     Show this help message
#   -v, --version  Show version information

# Strict mode
set -euo pipefail
IFS=$'\n\t'

# Script version
VERSION="1.0.0"

# Colors for output
autoload -U colors && colors

# Get the directory where the script is located
BASEDIR="${0:A:h}"

# Helper functions
print_error() { echo "${fg[red]}[ERROR]${reset_color} $1" >&2 }
print_warning() { echo "${fg[yellow]}[WARN]${reset_color} $1" >&2 }
print_info() { echo "${fg[green]}[INFO]${reset_color} $1" }
print_debug() { echo "${fg[blue]}[DEBUG]${reset_color} $1" }

# Usage information
usage() {
    cat << HELP
Usage: ${0:t} [options]

Options:
    -h, --help     Show this help message
    -v, --version  Show version information
HELP
}

# Version information
version() {
    echo "${0:t} version $VERSION"
}

# Create symlink function
create_symlink() {
    local src="$1"
    local dest="$2"

    [[ ! -e "$src" ]] && {
        print_error "Source file $src does not exist"
        return 1
    }

    # check if dest exist, delete it
    [[ -e "$dest" ]] && rm -rf "$dest"

    ln -sf "$src" "$dest"
    print_info "Created symlink for $(basename $src)"
}

# Setup symlinks function
setup_symlinks() {
    # vim
    create_symlink "${BASEDIR}/vim/vimrc" "${HOME}/.vimrc"

    # zsh
    create_symlink "${BASEDIR}/zsh/zshrc" "${HOME}/.zshrc"

    # tmux
    create_symlink "${BASEDIR}/tmux/tmux.conf" "${HOME}/.tmux.conf"

    # git
    create_symlink "${BASEDIR}/git/git-config" "${HOME}/.gitconfig"
    create_symlink "${BASEDIR}/git/git-template" "${HOME}/.git-template"


    # ssh
    create_symlink "${BASEDIR}/ssh/ssh-config" "${HOME}/.ssh/config"

    # Create symlinks for all the shell scripts under scripts directory
    for script in "${BASEDIR}/scripts"/*.sh; do
        create_symlink "$script" "${HOME}/.local/bin/$(basename -s .sh $script)"
    done
}

# Setup Vim configuration
setup_vim() {
    print_info "Setting up Vim configuration..."

    # Install vim-plug if not installed
    if [[ ! -f "$HOME/.vim/autoload/plug.vim" ]]; then
        print_info "Installing vim-plug..."
        curl -fLo "$HOME/.vim/autoload/plug.vim" --create-dirs \
            https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
    fi

    print_info "Vim configuration completed. Run :PlugInstall in Vim to install plugins"
}

# Setup Git configuration
setup_git_config() {
    local git_local="${HOME}/.gitconfig.local"
    local git_template="${BASEDIR}/git/git-template"

    # Only create local config if it doesn't exist
    if [[ ! -f "$git_local" ]]; then
        print_info "Setting up local Git configuration..."

        # Prompt for Git user information
        echo -n "Enter your Git user name: "
        read git_name
        echo -n "Enter your Git email: "
        read git_email

        # Create local config with user information
        cat > "$git_local" << EOF
[user]
	name = ${git_name}
	email = ${git_email}
EOF

        chmod 600 "$git_local"
        print_info "Created local Git configuration at $git_local"
    fi

    # Set proper permissions
    chmod 755 "$git_template/hooks"/*
    chmod 644 "$git_template/gitignore"
    chmod 644 "$git_template/commit-template"

    print_info "Git template directory set up at $git_template"
    print_info "Global git template configured in gitconfig"
}

# Setup zsh configuration
setup_zsh() {
    if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
        print_info "Installing oh-my-zsh..."
        sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
        # Install non-built-in plugins
        local ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
        # Install zsh-autosuggestions
        if [[ ! -d "${ZSH_CUSTOM}/plugins/zsh-autosuggestions" ]]; then
            print_info "Installing zsh-autosuggestions..."
            git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM}/plugins/zsh-autosuggestions
        fi

        # Install zsh-syntax-highlighting
        if [[ ! -d "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting" ]]; then
            print_info "Installing zsh-syntax-highlighting..."
            git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting
        fi
    else
        print_info "oh-my-zsh is already installed"
    fi
}

# Setup shell scripts configuration
setup_shell_scripts() {
    local scripts_dir="${HOME}/.local/bin"
    local dotfiles_scripts="${BASEDIR}/scripts"

    # Create scripts directories
    mkdir -p "$scripts_dir"
    mkdir -p "$dotfiles_scripts"

    # Add scripts directory to PATH if not already there
    if ! echo "$PATH" | tr ':' '\n' | grep -q "^${scripts_dir}$"; then
        # Update zshrc to include scripts directory
        echo '\n# User scripts path' >> "${BASEDIR}/zshrc"
        echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> "${BASEDIR}/zshrc"
    fi

    # Make scripts executable
    chmod +x "${dotfiles_scripts}/new-script.sh"
    chmod +x "${dotfiles_scripts}/script-template.sh"

    print_info "Shell scripts management set up at ~/.local/bin"
    print_info "Use 'new-script script-name' to create new scripts"
}

# OS-specific setup
setup_macos() {
    print_info "Configuring macOS specific settings..."
    # Add macOS specific configurations here

    # Check if Homebrew is installed, install if not
    if ! command -v brew >/dev/null 2>&1; then
        print_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    # Install required packages
    for pkg in git vim tmux zsh; do
        if ! command -v "$pkg" >/dev/null 2>&1; then
            print_info "Installing $pkg..."
            brew install "$pkg" || print_error "Failed to install $pkg"
        fi
    done
}

setup_linux() {
    log_info "Configuring Linux specific settings..."
    # Add Linux specific configurations here

    # Change shell to zsh
    print_info "Changing shell to zsh..."
    chsh -s $(which zsh)
}

# Main installation
main() {
    print_info "Starting dotfiles installation..."

    # Detect OS and run specific setup
    case "$(uname)" in
        "Darwin")
            setup_macos
            ;;
        "Linux")
            setup_linux
            ;;
    esac

    # Set up all components
    setup_vim
    setup_git_config
    setup_zsh
    setup_shell_scripts
    setup_symlinks

    print_info "Installation completed! Please restart your shell."
}

if [[ ! -o NO_EXEC ]]; then
    main "$@"
fi