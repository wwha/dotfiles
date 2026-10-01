#!/bin/zsh
# Link shared configuration without downloading dependencies or changing local overrides.
set -euo pipefail
BASEDIR="${0:A:h}"
dry_run=0
backup=0
ssh_config=0
while (( $# )); do
    case "$1" in
        -h|--help)
            print 'Usage: install.sh [--dry-run] [--backup] [--ssh] [--help | --version]'
            print 'Offline configuration links only. Conflicts stop installation unless --backup is specified.'
            print 'SSH config is opt-in. Run install-deps.sh separately for dependencies.'
            exit 0 ;;
        -v|--version) print 'install.sh version 1.2.0'; exit 0 ;;
        --dry-run) dry_run=1 ;;
        --backup) backup=1 ;;
        --ssh) ssh_config=1 ;;
        *) print -u2 "Unknown option: $1"; exit 1 ;;
    esac
    shift
done
[[ "$(uname)" == Darwin ]] || { print -u2 'Installation supports macOS only'; exit 1; }

typeset -a sources destinations
sources=("$BASEDIR/vim/vimrc" "$BASEDIR/zsh/zshrc" "$BASEDIR/tmux/tmux.conf" "$BASEDIR/git/git-config")
destinations=("$HOME/.vimrc" "$HOME/.zshrc" "$HOME/.tmux.conf" "$HOME/.gitconfig")
if (( ssh_config )); then
    sources+=("$BASEDIR/ssh/ssh-config")
    destinations+=("$HOME/.ssh/config")
fi

is_correct_link() {
    [[ -L "$2" && "${2:A}" == "${1:A}" ]]
}

# Inspect every link target and mutable parent before the first filesystem change.
typeset -a conflicts
conflicts=()
for i in {1..$#sources}; do
    src=${sources[$i]}
    dest=${destinations[$i]}
    [[ -f "$src" ]] || { print -u2 "Missing source: $src"; exit 1; }
    if [[ "${dest:h}" == "$HOME/.ssh" ]]; then
        if [[ -L "$HOME/.ssh" ]]; then
            print -u2 'Refusing to install through a symlinked ~/.ssh directory.'; exit 1
        fi
        if [[ -e "$HOME/.ssh" && ! -d "$HOME/.ssh" ]]; then
            print -u2 '~/.ssh exists and is not a directory.'; exit 1
        fi
    fi
    if ! is_correct_link "$src" "$dest" && { [[ -e "$dest" ]] || [[ -L "$dest" ]]; }; then
        conflicts+=("$dest")
    fi
done
if [[ -e "$HOME/.dotfiles_backups" || -L "$HOME/.dotfiles_backups" ]]; then
    [[ -d "$HOME/.dotfiles_backups" && ! -L "$HOME/.dotfiles_backups" ]] || {
        print -u2 'Refusing to use a non-directory or symlinked ~/.dotfiles_backups.'; exit 1
    }
    [[ "$(stat -f '%u' "$HOME/.dotfiles_backups")" == "$EUID" ]] || {
        print -u2 '~/.dotfiles_backups must be owned by the current user.'; exit 1
    }
    backup_mode=$(stat -f '%Lp' "$HOME/.dotfiles_backups")
    (( (8#$backup_mode & 8#077) == 0 )) || {
        print -u2 '~/.dotfiles_backups must not be accessible by group or others.'; exit 1
    }
fi
if (( ${#conflicts} && ! backup && ! dry_run )); then
    print -u2 'Conflicts found; nothing was changed. Review with --dry-run or explicitly replace with --backup.'
    printf '  %s\n' "${conflicts[@]}" >&2
    exit 1
fi

if (( dry_run )); then
    for i in {1..$#sources}; do
        src=${sources[$i]}; dest=${destinations[$i]}
        if is_correct_link "$src" "$dest"; then
            print -r -- "Already linked: $dest"
        elif [[ -e "$dest" || -L "$dest" ]]; then
            print -r -- "Would back up: $dest"
            print -r -- "Would link: $dest -> $src"
        else
            print -r -- "Would link: $dest -> $src"
        fi
    done
    if [[ ! -L "$HOME/.git-template" && ( ! -e "$HOME/.git-template" || -d "$HOME/.git-template" ) ]]; then
        for name in gitignore commit-template; do
            dest="$HOME/.git-template/$name"
            [[ -e "$dest" || -L "$dest" ]] || print -r -- "Would link: $dest -> $BASEDIR/git/git-template/$name"
        done
    fi
    exit 0
fi

backup_dir=''
if (( backup && ${#conflicts} )); then
    (umask 077; mkdir -p "$HOME/.dotfiles_backups")
    backup_dir=$(mktemp -d "$HOME/.dotfiles_backups/$(date +%Y%m%d_%H%M%S).XXXXXX")
    for dest in "${conflicts[@]}"; do
        mv "$dest" "$backup_dir/${dest:t}"
        print -r -- "Backup: $backup_dir/${dest:t}"
    done
fi

for i in {1..$#sources}; do
    src=${sources[$i]}; dest=${destinations[$i]}
    if is_correct_link "$src" "$dest"; then
        print -r -- "Already linked: $dest"
    else
        mkdir -p "${dest:h}"
        ln -s "$src" "$dest"
        print -r -- "Linked: $dest -> $src"
    fi
done

# Preserve legacy template symlinks, custom files and hooks. Fill only missing defaults.
if [[ -L "$HOME/.git-template" || ( -e "$HOME/.git-template" && ! -d "$HOME/.git-template" ) ]]; then
    print -r -- 'Preserving existing ~/.git-template.'
else
    for name in gitignore commit-template; do
        dest="$HOME/.git-template/$name"
        src="$BASEDIR/git/git-template/$name"
        if [[ ! -e "$dest" && ! -L "$dest" ]]; then
            mkdir -p "${dest:h}"
            ln -s "$src" "$dest"
            print -r -- "Linked: $dest -> $src"
        fi
    done
fi
print 'Local overrides and legacy command links are unchanged. See README.md before activation.'
