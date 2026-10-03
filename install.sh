#!/bin/zsh
# Link shared configuration or explicitly manage its dependencies.
set -euo pipefail
BASEDIR="${0:A:h}"
mode=link
dry_run=0
backup=0
ssh_config=0

if [[ "${1:-}" == deps || "${1:-}" == update ]]; then
    mode=$1
    shift
fi

while (( $# )); do
    case "$1" in
        -h|--help)
            print 'Usage: install.sh [--dry-run] [--backup] [--ssh]'
            print '       install.sh deps | update'
            print 'Default: previewable Stow links only. deps installs missing dependencies; update upgrades them.'
            exit 0 ;;
        -v|--version) print 'install.sh version 2.0.0'; exit 0 ;;
        --dry-run) dry_run=1 ;;
        --backup) backup=1 ;;
        --ssh) ssh_config=1 ;;
        *) print -u2 "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

[[ "$(uname)" == Darwin ]] || { print -u2 'Installation supports macOS only'; exit 1; }

if [[ "$mode" == deps || "$mode" == update ]]; then
    (( ! dry_run && ! backup && ! ssh_config )) || {
        print -u2 'Linking options cannot be combined with deps or update.'; exit 1
    }
    command -v brew >/dev/null || { print -u2 'Install Homebrew first: https://brew.sh'; exit 1; }
    if [[ "$mode" == deps ]]; then
        HOMEBREW_BUNDLE_NO_UPGRADE=1 brew bundle install --file="$BASEDIR/Brewfile"
        if [[ ! -r "$HOME/.vim/autoload/plug.vim" ]]; then
            plugin_tmp=$(mktemp "${TMPDIR:-/tmp}/vim-plug.XXXXXX")
            if ! curl --fail --location --silent --show-error \
                https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim -o "$plugin_tmp"; then
                rm -f "$plugin_tmp"
                exit 1
            fi
            mkdir -p "$HOME/.vim/autoload"
            mv "$plugin_tmp" "$HOME/.vim/autoload/plug.vim"
        fi
        if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
            [[ ! -e "$HOME/.oh-my-zsh" && ! -L "$HOME/.oh-my-zsh" ]] || {
                print -u2 'Refusing to replace an existing non-directory ~/.oh-my-zsh.'; exit 1
            }
            omz_tmp=$(mktemp -d "$HOME/.oh-my-zsh.XXXXXX")
            rmdir "$omz_tmp"
            if ! git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$omz_tmp"; then
                rm -rf "$omz_tmp"
                exit 1
            fi
            mv "$omz_tmp" "$HOME/.oh-my-zsh"
        fi
        if command -v vim >/dev/null && [[ -r "$HOME/.vim/autoload/plug.vim" ]]; then
            vim -Nu "$BASEDIR/stow/vim/.vimrc" -i NONE -es -c PlugInstall -c qall
        fi
    else
        brew update
        brew bundle upgrade --file="$BASEDIR/Brewfile"
        if [[ -r "$HOME/.vim/autoload/plug.vim" ]]; then
            plugin_tmp=$(mktemp "${TMPDIR:-/tmp}/vim-plug.XXXXXX")
            if ! curl --fail --location --silent --show-error \
                https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim -o "$plugin_tmp"; then
                rm -f "$plugin_tmp"
                exit 1
            fi
            mkdir -p "$HOME/.vim/autoload"
            mv "$plugin_tmp" "$HOME/.vim/autoload/plug.vim"
        fi
        if [[ -x "$HOME/.oh-my-zsh/tools/upgrade.sh" ]]; then
            zsh "$HOME/.oh-my-zsh/tools/upgrade.sh"
        fi
        if [[ -r "$HOME/.vim/autoload/plug.vim" ]] && command -v vim >/dev/null; then
            vim -Nu "$BASEDIR/stow/vim/.vimrc" -i NONE -es -c PlugUpdate -c qall
        fi
    fi
    plugin_root="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins"
    for plugin in zsh-autosuggestions zsh-syntax-highlighting; do
        plugin_dir="$plugin_root/$plugin"
        if [[ "$mode" == deps ]]; then
            if [[ ! -e "$plugin_dir" && ! -L "$plugin_dir" ]]; then
                mkdir -p "$plugin_root"
                plugin_tmp=$(mktemp -d "$plugin_root/.$plugin.XXXXXX")
                rmdir "$plugin_tmp"
                if ! git clone --depth=1 "https://github.com/zsh-users/$plugin.git" "$plugin_tmp"; then
                    rm -rf "$plugin_tmp"
                    exit 1
                fi
                mv "$plugin_tmp" "$plugin_dir"
            fi
        elif [[ -d "$plugin_dir/.git" ]]; then
            git -C "$plugin_dir" pull --ff-only
        fi
    done
    exit 0
fi

command -v stow >/dev/null || {
    print -u2 'GNU Stow is required. Run ./install.sh deps, then retry.'; exit 1
}

packages=(zsh git vim tmux)
(( ssh_config )) && packages+=(ssh)
typeset -a conflicts
conflicts=()

is_correct_link() {
    [[ -L "$2" && "${2:A}" == "${1:A}" ]]
}

template_pre_commit="$HOME/.git-template/hooks/pre-commit"
template_pre_commit_local="$HOME/.git-template/hooks/pre-commit.local"
template_pre_commit_source="$BASEDIR/stow/git/.git-template/hooks/pre-commit"
if [[ -e "$template_pre_commit" || -L "$template_pre_commit" ]] && \
        ! is_correct_link "$template_pre_commit_source" "$template_pre_commit" && \
        { [[ -e "$template_pre_commit_local" ]] || [[ -L "$template_pre_commit_local" ]]; }; then
    print -u2 'Cannot preserve ~/.git-template/hooks/pre-commit because pre-commit.local already exists.'
    exit 1
fi

for package in "${packages[@]}"; do
    package_dir="$BASEDIR/stow/$package"
    [[ -d "$package_dir" ]] || { print -u2 "Missing Stow package: $package_dir"; exit 1; }
    while IFS= read -r -d '' src; do
        rel=${src#"$package_dir"/}
        dest="$HOME/$rel"
        parent=${dest:h}
        blocked=0
        while [[ "$parent" == "$HOME"/* ]]; do
            if [[ -L "$parent" ]]; then
                conflicts+=("$parent")
                blocked=1
                break
            fi
            if [[ -e "$parent" && ! -d "$parent" ]]; then
                conflicts+=("$parent")
                blocked=1
                break
            fi
            parent=${parent:h}
        done
        if (( ! blocked )) && ! is_correct_link "$src" "$dest" && { [[ -e "$dest" ]] || [[ -L "$dest" ]]; }; then
            conflicts+=("$dest")
        fi
    done < <(find "$package_dir" -type f -print0)
done

# De-duplicate blockers while preserving the order in which Stow will encounter them.
typeset -U conflicts
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
    for conflict_path in "${conflicts[@]}"; do print -r -- "Would back up: $conflict_path"; done
    for package in "${packages[@]}"; do
        package_dir="$BASEDIR/stow/$package"
        while IFS= read -r -d '' src; do
            rel=${src#"$package_dir"/}
            dest="$HOME/$rel"
            if is_correct_link "$src" "$dest"; then
                link_value=$(readlink "$dest")
                if [[ "$link_value" == *"/stow/$package/$rel" ]]; then
                    print -r -- "Already linked: $dest"
                else
                    print -r -- "Would retarget legacy link: $dest -> $src"
                fi
            else
                print -r -- "Would link: $dest -> $src"
            fi
        done < <(find "$package_dir" -type f -print0)
    done
    exit 0
fi

if (( backup && ${#conflicts} )); then
    (umask 077; mkdir -p "$HOME/.dotfiles_backups")
    backup_dir=$(mktemp -d "$HOME/.dotfiles_backups/$(date +%Y%m%d_%H%M%S).XXXXXX")
    for dest in "${conflicts[@]}"; do
        if [[ "$dest" == "$template_pre_commit" ]] && ! is_correct_link "$template_pre_commit_source" "$dest"; then
            mkdir -p "${template_pre_commit_local:h}"
            mv "$dest" "$template_pre_commit_local"
            print -r -- "Preserved private hook: $template_pre_commit_local"
            continue
        fi
        rel=${dest#"$HOME"/}
        mkdir -p "$backup_dir/${rel:h}"
        mv "$dest" "$backup_dir/$rel"
        print -r -- "Backup: $backup_dir/$rel"
    done
fi

# Retarget recognized old-layout links to the package source before Stow runs.
for package in "${packages[@]}"; do
    package_dir="$BASEDIR/stow/$package"
    while IFS= read -r -d '' src; do
        rel=${src#"$package_dir"/}
        dest="$HOME/$rel"
        if is_correct_link "$src" "$dest"; then
            link_value=$(readlink "$dest")
            if [[ "$link_value" != *"/stow/$package/$rel" ]]; then
                ln -sfn "$src" "$dest"
                print -r -- "Retargeted legacy link: $dest -> $src"
            fi
        fi
    done < <(find "$package_dir" -type f -print0)
done

stow --no-folding --dir="$BASEDIR/stow" --target="$HOME" "${packages[@]}"
