#!/bin/zsh
# Link shared configuration without downloading dependencies or changing local overrides.
set -euo pipefail
BASEDIR="${0:A:h}"
dry_run=0
case "${1:-}" in
    -h|--help)
        print 'Usage: install.sh [--dry-run | --help | --version]'
        print 'Offline configuration links only. Run install-deps.sh separately for dependencies.'
        exit 0 ;;
    -v|--version) print 'install.sh version 1.1.0'; exit 0 ;;
    --dry-run) dry_run=1 ;;
    '') ;;
    *) print -u2 "Unknown option: $1"; exit 1 ;;
esac
(( $# <= 1 )) || { print -u2 'Too many arguments'; exit 1; }
[[ "$(uname)" == Darwin ]] || { print -u2 'Installation supports macOS only'; exit 1; }

create_symlink() {
    local src="$1" dest="$2" backup_dir
    [[ -e "$src" ]] || { print -u2 "Missing source: $src"; return 1; }
    if [[ -L "$dest" && "${dest:A}" == "${src:A}" ]]; then
        print -r -- "Already linked: $dest"
        return
    fi
    if [[ -e "$dest" || -L "$dest" ]]; then
        if (( dry_run )); then
            print -r -- "Would back up: $dest"
        else
            # mv preserves symlinks themselves, including dangling links.
            (umask 077; mkdir -p "$HOME/.dotfiles_backups")
            backup_dir=$(mktemp -d "$HOME/.dotfiles_backups/$(date +%Y%m%d_%H%M%S).XXXXXX")
            mv "$dest" "$backup_dir/"
            print -r -- "Backup: $backup_dir/${dest:t}"
        fi
    fi
    if (( dry_run )); then
        print -r -- "Would link: $dest -> $src"
    else
        mkdir -p "${dest:h}"
        ln -s "$src" "$dest"
        print -r -- "Linked: $dest -> $src"
    fi
}

create_symlink "$BASEDIR/vim/vimrc" "$HOME/.vimrc"
create_symlink "$BASEDIR/zsh/zshrc" "$HOME/.zshrc"
create_symlink "$BASEDIR/tmux/tmux.conf" "$HOME/.tmux.conf"
create_symlink "$BASEDIR/git/git-config" "$HOME/.gitconfig"

# Preserve legacy template symlinks, custom files and hooks. Fill missing defaults
# in a real directory so a partially completed fresh installation can be retried.
if [[ -L "$HOME/.git-template" || ( -e "$HOME/.git-template" && ! -d "$HOME/.git-template" ) ]]; then
    print -r -- 'Preserving existing ~/.git-template.'
else
    for name in gitignore commit-template; do
        if [[ ! -e "$HOME/.git-template/$name" && ! -L "$HOME/.git-template/$name" ]]; then
            create_symlink "$BASEDIR/git/git-template/$name" "$HOME/.git-template/$name"
        fi
    done
fi
if (( ! dry_run )) && [[ ! -d "$HOME/.ssh" ]]; then
    (umask 077; mkdir -p "$HOME/.ssh")
fi
create_symlink "$BASEDIR/ssh/ssh-config" "$HOME/.ssh/config"
print 'Local overrides and legacy command links are unchanged. See README.md before activation.'
