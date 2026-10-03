#!/bin/zsh
# Prepare integration plugins in a disposable GitHub Actions HOME, without linking.
set -euo pipefail
repo="${0:A:h:h}"
ci_home="${1:?Usage: prepare-ci.zsh <directory under RUNNER_TEMP>}"
[[ -n "${RUNNER_TEMP:-}" && "$ci_home" == "$RUNNER_TEMP"/* && "$ci_home" != "$HOME" ]] || {
    print -u2 'CI dependencies must use a separate HOME under RUNNER_TEMP.'
    exit 1
}
[[ ! -e "$ci_home" && ! -L "$ci_home" ]] || {
    print -u2 'CI dependency HOME must not already exist.'
    exit 1
}
export HOME="$ci_home" ZDOTDIR="$ci_home"
mkdir -p "$HOME/.vim/autoload"
git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$HOME/.oh-my-zsh"
curl --fail --location --silent --show-error \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim \
    -o "$HOME/.vim/autoload/plug.vim"
/usr/bin/vim -Nu "$repo/stow/vim/.vimrc" -i NONE -es -c 'PlugInstall --sync' -c qall
for plugin in ale fzf.vim vim-tmux-navigator; do
    [[ -d "$HOME/.vim/plugged/$plugin" ]] || {
        print -u2 "Missing CI Vim plugin: $plugin"
        exit 1
    }
done
