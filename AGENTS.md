# Working on dotfiles

This repository manages a personal macOS environment through shared configuration and symlinks.

Dependencies are managed with Homebrew through the Brewfile.

Preserve local overrides (`*.local`, `local.*`) and credentials outside Git.
Never validate changes by running install, restore, network settings, or sourcing
interactive shell configuration against the user's HOME; use isolated tests.

## Verification commands

- `zsh tests/check.zsh --static`: syntax and Git configuration checks.
- `zsh tests/check.zsh --all`: isolated behavior tests on macOS.

## Task-specific instructions

- When changing scripts or configuration, or validating changes, read
  [Testing](docs/agents/testing.md).
- When preparing a PR or working in Codex Cloud, read
  [Workflow](docs/agents/workflow.md).
- When changing installation or backup semantics, read
  [Project context](docs/CONTEXT.md).
