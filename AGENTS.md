# Working on dotfiles

This repository manages a personal macOS environment through shared configuration
and symlinks. Read CONTEXT.md when changing installation or backup semantics.

## Verification

- Run `zsh tests/check.zsh --static` for syntax and Git configuration checks.
- On macOS, run `zsh tests/check.zsh --all` for isolated behavior tests as well.
- In Codex Cloud, run static checks and report macOS behavior tests as pending CI.
- For script changes, add regression coverage through the command-line interface
  in `tests/test_scripts.py`. Use temporary copies and command substitutes for
  package downloads, system settings, and notifications.

## Boundaries

- Personal installation supports macOS only. Cloud is a development environment.
- Never run install, restore, network settings, or source interactive shell
  configuration against the user's HOME to validate changes. Use the test suite.
- Preserve local overrides (`*.local`, `local.*`) and credentials outside Git.
- Keep Zsh syntax; ShellCheck does not validate Zsh. Git hooks may rewrite files
  and must not be invoked as the CI check command.
- Submit changes through a PR; the owner merges after required CI passes.

For Cloud setup and branch protection, follow the workflow section in README.md.

## Agent skills

### Issue tracker

Issues live in GitHub Issues. Read `docs/agents/issue-tracker.md`
before reading or publishing issues.

### Triage labels

Use the five canonical triage labels. Read `docs/agents/triage-labels.md`
before applying triage labels.

### Domain docs

This repo uses a single-context layout. Read `docs/agents/domain.md`
before exploring domain concepts or architectural decisions.
