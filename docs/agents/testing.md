# Testing

Run `zsh tests/check.zsh --static`.
On macOS, also run `zsh tests/check.zsh --all`.
In Codex Cloud, run static checks and report macOS behavior tests as pending CI.

For script changes, add regression coverage through the command-line interface
in `tests/test_scripts.py`. Use temporary copies and command substitutes for
package downloads, system settings, and notifications.

Preserve Zsh syntax; ShellCheck does not validate Zsh.
Use the check script for CI verification; Git hooks may rewrite files.
