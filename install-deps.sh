#!/bin/zsh
# Explicit dependency setup. Homebrew validates formula downloads; this script
# does not execute remote shell installers or clone floating Git branches.
set -euo pipefail
BASEDIR="${0:A:h}"
case "${1:-}" in
    -h|--help) print 'Usage: install-deps.sh'; exit 0 ;;
    '') ;;
    *) print -u2 "Unknown option: $1"; exit 1 ;;
esac
[[ "$(uname)" == Darwin ]] || { print -u2 'Dependency installation supports macOS only'; exit 1; }
command -v brew >/dev/null || { print -u2 'Install Homebrew first: https://brew.sh'; exit 1; }
brew bundle --file="$BASEDIR/Brewfile"
print 'Homebrew dependencies installed. Vim plugins are installed explicitly from inside Vim with :PlugInstall.'
