#!/bin/zsh
#
# Script Name: backup.sh
# Description: Dotfiles backup and recovery script
# Author: $(git config user.name)
# Date Created: 2024-12-09
# Last Modified: 2024-12-09

# Strict mode
set -euo pipefail
IFS=$'\n\t'

# Script version
VERSION="1.0.0"

# Colors for output
autoload -U colors && colors

# Get the directory where the script is located
BASEDIR="${0:A:h}"
BACKUP_DIR="$HOME/dotfiles_backup/$(date +%Y%m%d_%H%M%S)"

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
    -b, --backup   Backup dotfiles
    -r, --recover  Recover from backup
    -l, --list     List available backups
    -h, --help     Show this help message
    -v, --version  Show version information
HELP
}

# Version information
version() {
    echo "${0:t} version $VERSION"
}

# List available backups
list_backups() {
    local backup_root="$HOME/dotfiles_backup"
    if [[ -d "$backup_root" ]]; then
        print_info "Available backups:"
        ls -lt "$backup_root" | grep '^d' | awk '{print $9}'
    else
        print_warning "No backups found in $backup_root"
    fi
}

# Backup function
backup_dotfiles() {
    print_info "Starting backup process..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Backup dotfiles excluding .git directory
    rsync -av --progress "$BASEDIR/" "$BACKUP_DIR/" \
        --exclude='.git' \
        --exclude='.DS_Store' \
        --exclude='*.swp' \
        --exclude='*.swo' \
        --exclude='*~'

    print_info "Backup completed: $BACKUP_DIR"
}

# Recover function
recover_from_backup() {
    local backup_root="$HOME/dotfiles_backup"

    # List available backups
    list_backups

    # Prompt for backup selection
    echo -n "Enter backup directory name to recover from: "
    read backup_name

    local selected_backup="$backup_root/$backup_name"

    if [[ ! -d "$selected_backup" ]]; then
        print_error "Invalid backup directory: $backup_name"
        exit 1
    fi

    print_info "Recovering from: $selected_backup"

    # Backup current dotfiles before recovery
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local pre_recovery_backup="$BASEDIR.pre_recovery.$timestamp"
    mv "$BASEDIR" "$pre_recovery_backup"
    print_info "Current dotfiles backed up to: $pre_recovery_backup"

    # Recover from backup
    mkdir -p "$BASEDIR"
    rsync -av --progress "$selected_backup/" "$BASEDIR/" \
        --exclude='.git' \
        --exclude='.DS_Store'

    print_info "Recovery completed successfully!"
}

# Main process
main() {
    case "$1" in
        -b|--backup)
            backup_dotfiles
            ;;
        -r|--recover)
            recover_from_backup
            ;;
        -l|--list)
            list_backups
            ;;
        -h|--help)
            usage
            ;;
        -v|--version)
            version
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
}

# Parse command line arguments
if [[ $# -eq 0 ]]; then
    usage
    exit 1
else
    main "$1"
fi