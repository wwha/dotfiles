# Compatibility migration: phase one

This phase prepares a safer installer and fixes configuration defects. It does
not migrate the current Mac. Development happens in a separate worktree; the
active checkout, HOME links and running applications stay unchanged. Owner
confirmation of real-machine migration is required before a second deletion PR.

## Impact inventory

Changes below take effect only when the Mac reads the new files. Do not pull,
checkout or edit these changes in the active repository as a way to preview them.

| Existing entry | Phase-one behavior / new entry | Migration and rollback |
| --- | --- | --- |
| `install.sh` | Offline; full conflict preflight; conflicts stop by default; explicit `--backup`; SSH link is opt-in via `--ssh` | Review `--dry-run` first. Restore displaced objects from printed private backup paths. |
| Automatic package downloads | Explicit `install-deps.sh` and Brewfile; no fetched shell installer or floating Git clone | Homebrew can upgrade packages. Vim `:PlugInstall` executes declared third-party plugin code; review declarations before running. |
| `~/.git-template` | Existing links/files/hooks preserved; missing defaults in a real directory are filled; fresh installs get no hooks | Preserve old checkout while its template link is in use. Disable hooks only as a separate migration. |
| Global Git ignore | Removes broad database/dependency exclusions; keeps OS/editor files | Previously ignored project artifacts may now appear untracked. Check worktree status and move project-specific patterns into each project. |
| Git local include | Loaded last, so local values now win | Review duplicate settings; restore the previous config link to roll back. |
| `new-script`, `script-template`, `set-wifi-dns` | Existing links and tracked sources retained; not installed for new users | Copy tools to private storage and repoint links before any later deletion. Network tool still changes IP and DNS. |
| Conda/NVM/API keys | Removed from shared startup; optional local initialization examples | Add only the paths and secrets file used on this Mac to `.zshrc.local`; check each initializer once. |
| Bun/bunx | Shared completion, BUN_INSTALL and PATH initialization removed; programs remain installed | New terminals may not find commands installed only in ~/.bun/bin. Restore initialization via the optional local snippet in README. |
| ShellCheck | Removed from Brewfile, Vim shell linters and the retained pre-commit hook | Existing linked hook sources change on activation; already copied project hooks and installed programs are untouched. Zsh syntax checks remain. |
| `~/.zshrc.local`, `~/.vimrc.local`, `~/.tmux.conf.local` | Existing tail overrides remain | Review their contents before activation; restore saved versions for rollback. |
| Rime and automatic tmux | No startup prompt or automatic tmux session; Rime update remains a manual function | Start tmux explicitly. Source the Rime helper and run `rime_ice_update` when wanted. |
| Vim | Recovery defaults enabled; save-time fix/trim, file templates and OSC52 are opt-in; shell ALE linters disabled | Existing modified buffers are protected by normal `:bdelete` prompting. Review Vim plugin declarations before `:PlugInstall`. |
| tmux | Clipboard is `external`: tmux copy commands may reach the terminal, applications inside tmux cannot set outer clipboard | Test a separate server before reloading a long-lived one; existing sessions are not reloaded automatically. |
| Network script | Requires explicit interface and address values; original private network values removed | Review arguments carefully before running because it changes system network settings. |
| `backup.sh` | Legacy snapshot/overlay recovery retained unchanged | Keep existing snapshots. Verify private/system backup before retiring this script in phase two. |

## Before any real-machine activation

These are **future manual steps**, not actions performed by this PR or its tests.

1. Keep an existing terminal and tmux session open. Record the active checkout's
   commit, uncommitted changes, and every managed link's literal target. Preserve
   that checkout at its current state; do not use `git reset` or discard changes.
2. Create a private backup directory outside the repository (`umask 077` and
   `mktemp -d` under HOME). Copy the active checkout including uncommitted files,
   HOME local overrides, `.api_keys`, and any other private configuration you
   will change. Preserve symlinks as links (`cp -pPR`) and separately copy the
   contents of external targets needed for recovery. Keep a record of absent
   files too. Do not publish the backup or copy it into Git.
3. Inspect existing local overrides because the new Zsh/Vim/tmux entry points
   will now execute them. Check the Git ignore impact in representative projects.
   Confirm a separate private/system backup actually contains recoverable files;
   its existence is not implied by this repository.
4. Prepare the reviewed revision in a **permanent separate checkout**, not an
   ephemeral development worktree. Run its `install.sh --dry-run` and review every
   target. Leave old template and command links pointed at the preserved checkout.
5. Only after explicit activation approval, run the offline installer there. Save
   its printed conflict backup paths. Dependency setup is a separate choice; it
   can change installed package versions, so do not run it just to repoint links.
6. Verify in new processes: Git identity and ignores, SSH effective settings and a
   known host, Vim startup and edits, shell commands and initializers. Test tmux
   with a separate socket before reloading the existing server. Keep old processes
   open until validation is complete; do not force a shell restart or kill sessions.

## Rollback

For each changed HOME destination, first confirm it is still the newly installed
symlink and has no later user edits. Unlink that symlink, then move the saved
original object from its printed conflict backup path back to the destination.
This restores files, directories and symlink text; relative symlinks resolve
correctly again at their original location. For originally absent destinations,
remove only the newly created links. Restore separately saved local files if they
were edited, and keep the preserved old checkout available for restored links.

A link backup alone cannot undo edits to its target. If the active checkout was
updated despite the separation above, recover its files from the pre-activation
copy first, preserving any later work separately. Git restores only committed
content. Do not overlay the legacy `backup.sh` snapshot into an active checkout
as an automatic rollback.

Open a new terminal/Vim against restored files. A tmux server already reloaded
with the new configuration may retain options absent from the old config; validate
the old config on a separate server and restore changed options explicitly without
killing existing sessions. Configuration rollback does not undo package upgrades.

## Gate for phase two

The owner must confirm the real environment works and the following migrations
are complete before old tracked files are deleted:

- Move only needed machine initializers into local files. Check Conda/NVM and
  secret loading. Bun remains opt-in through local configuration.
- If retaining the old script generator, copy **both** generator and template into
  the same private scripts directory, plus the network script if needed. Repoint
  each command link and test help/generation without changing network settings.
- Replace the legacy template symlink with a reviewed directory retaining ignore
  and commit-template files but no default hooks. Existing project hooks are copies:
  inspect and disable only the intended hooks in each project, separately. Do not
  scan and delete hooks globally.
- Move project-specific ignore rules to the relevant projects. Confirm Rime
  updates are explicit and startup no longer prompts. Confirm the replacement
  backup can restore private files.
- Record successful checks and rollback location in the second PR. Passing isolated
  tests or merging phase one alone is not migration confirmation.

## Practice references

[GNU Stow](https://www.gnu.org/software/stow/) documents the symlink approach;
[Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile) documents dependency
lists. [Git's ignore documentation](https://git-scm.com/docs/gitignore) distinguishes
shared project rules from personal global patterns. This phase retains the current
layout and postpones behavior removal until migration is verified.
