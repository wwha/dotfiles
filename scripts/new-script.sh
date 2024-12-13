#!/bin/zsh

set -euo pipefail
setopt SH_WORD_SPLIT

# Colors for output
autoload -U colors && colors

# Script directory
SCRIPTS_DIR="${HOME}/.local/bin"
DOTFILES_SCRIPTS="${HOME}/.dotfiles/scripts"

# Helper functions
print_error() { echo "${fg[red]}ERROR:${reset_color} $1" >&2 }
print_info() { echo "${fg[green]}INFO:${reset_color} $1" }

# Usage information
usage() {
    cat << HELP
Usage: ${0:t} <script-name> [description]

Arguments:
    script-name     Name of the new script (required)
    description     Brief description of the script (optional)

Example:
    ${0:t} backup-photos "Backup photos to external drive"
HELP
}

# Validate script name
validate_name() {
    local name="$1"
    if [[ ! "$name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        print_error "Invalid script name. Use only letters, numbers, underscores, and hyphens."
        exit 1
    fi
}

# Main logic
if (( $# < 1 )); then
    usage
    exit 1
fi

script_name="$1"
description="${2:-Script description}"

# Add .sh extension for dotfiles but not for local bin
dotfiles_script_path="${DOTFILES_SCRIPTS}/${script_name}.sh"
local_script_path="${SCRIPTS_DIR}/${script_name}"

# Validate script name
validate_name "$script_name"

# Check if script already exists (either version)
if [[ -e "$local_script_path" ]] || [[ -e "$dotfiles_script_path" ]]; then
    print_error "Script $script_name already exists"
    exit 1
fi

# Create new script from template
cp "${DOTFILES_SCRIPTS}/script-template.sh" "$dotfiles_script_path"

# Update script name and description
sed -i '' \
    -e "s/script-template.sh/${script_name}.sh/" \
    -e "s/Template for shell scripts/$description/" \
    -e "s/\$(git config user.name)/$(git config user.name)/" \
    -e "s/\$(date +%Y-%m-%d)/$(date +%Y-%m-%d)/" \
    "$dotfiles_script_path"

# Make script executable
chmod +x "$dotfiles_script_path"

# Create symlink in .local/bin
ln -sf "$dotfiles_script_path" "$local_script_path"

print_info "Created new script: $dotfiles_script_path"
print_info "Created symlink: $local_script_path"

# Open in default editor if EDITOR is set
if [[ -n "${EDITOR:-}" ]]; then
    print_info "Opening script in editor..."
    $EDITOR "$dotfiles_script_path"
fi
