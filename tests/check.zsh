#!/bin/zsh
set -euo pipefail
cd "${0:A:h:h}"
mode=${1:---static}
case "$mode" in
    --static|--all|--ci) ;;
    *) print -u2 'Usage: zsh tests/check.zsh [--static|--all|--ci]'; exit 1 ;;
esac
while IFS= read -r -d '' file; do
    [[ -f "$file" ]] || continue
    case "$file" in
        *.sh|*.zsh|stow/zsh/.zshrc|stow/git/.git-template/hooks/*) zsh -f -n "$file" ;;
    esac
done < <(git ls-files -z --cached --others --exclude-standard)
git config --file stow/git/.gitconfig --no-includes --list >/dev/null
if [[ "$mode" == --all || "$mode" == --ci ]]; then
    [[ "$(uname)" == Darwin ]] || { print -u2 'Behavior tests require macOS'; exit 1; }
    if [[ "$mode" == --ci ]]; then
        python3 - <<'PY'
import sys
import unittest

suite = unittest.defaultTestLoader.discover('tests')
result = unittest.TextTestRunner(verbosity=2).run(suite)
if result.skipped:
    print('CI requires all behavior tests to run; skipped tests are failures.', file=sys.stderr)
sys.exit(not result.wasSuccessful() or bool(result.skipped))
PY
    else
        python3 -m unittest discover -s tests -v
    fi
fi
