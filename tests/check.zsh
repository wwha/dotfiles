#!/bin/zsh
set -euo pipefail
cd "${0:A:h:h}"
mode=${1:---static}
case "$mode" in
    --static|--all) ;;
    *) print -u2 'Usage: zsh tests/check.zsh [--static|--all]'; exit 1 ;;
esac
while IFS= read -r -d '' file; do
    [[ -f "$file" ]] || continue
    case "$file" in
        *.sh|*.zsh|stow/zsh/.zshrc|stow/git/.git-hooks/*) zsh -f -n "$file" ;;
    esac
done < <(git ls-files -z --cached --others --exclude-standard)
git config --file stow/git/.gitconfig --no-includes --list >/dev/null
if [[ "$mode" == --all ]]; then
    [[ "$(uname)" == Darwin ]] || { print -u2 'Behavior tests require macOS'; exit 1; }
    python3 -m unittest discover -s tests -v
fi
