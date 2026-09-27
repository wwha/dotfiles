#!/bin/zsh
# Explicit, network-enabled dependency setup. Never links shared configuration.
set -euo pipefail
BASEDIR="${0:A:h}"
case "${1:-}" in
    -h|--help) print 'Usage: install-deps.sh (requires Homebrew; installs Brewfile and editor/shell plugins)'; exit 0 ;;
    '') ;;
    *) print -u2 "Unknown option: $1"; exit 1 ;;
esac
(( $# <= 1 )) || { print -u2 'Too many arguments'; exit 1; }
[[ "$(uname)" == Darwin ]] || { print -u2 'Dependency installation supports macOS only'; exit 1; }
if ! command -v brew >/dev/null; then
    print -u2 'Install Homebrew first: https://brew.sh'
    exit 1
fi
print_info() { print -r -- "$1"; }
print_warning() { print -r -- "$1"; }

setup_vim() {
    print_info "Setting up Vim configuration..."

    # Install vim-plug if not installed
    if [[ ! -f "$HOME/.vim/autoload/plug.vim" ]]; then
        print_warning "Proceeding to download and install vim-plug from GitHub..."
        curl -fLo "$HOME/.vim/autoload/plug.vim" --create-dirs \
            https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
    fi

    print_info "Vim configuration completed. Run :PlugInstall in Vim to install plugins"
}

setup_zsh() {
    if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
        print_warning "Proceeding to download and install Oh-My-Zsh from GitHub..."
        print_info "Existing .zshrc and default shell will be preserved."
        local installer
        installer=$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)
        KEEP_ZSHRC=yes RUNZSH=no CHSH=no sh -c "$installer" "" --unattended
    else
        print_info "oh-my-zsh is already installed"
    fi

    # Install non-built-in plugins
    local ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
    # Install zsh-autosuggestions
    if [[ ! -d "${ZSH_CUSTOM}/plugins/zsh-autosuggestions" ]]; then
        print_info "Installing zsh-autosuggestions..."
        git clone https://github.com/zsh-users/zsh-autosuggestions "${ZSH_CUSTOM}/plugins/zsh-autosuggestions"
    fi

    # Install zsh-syntax-highlighting
    if [[ ! -d "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting" ]]; then
        print_info "Installing zsh-syntax-highlighting..."
        git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "${ZSH_CUSTOM}/plugins/zsh-syntax-highlighting"
    fi
}

brew bundle --file="$BASEDIR/Brewfile"
setup_vim
setup_zsh
