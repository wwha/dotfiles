# Stow migration

This pull request changes the repository layout. It does not migrate the active
Mac. Existing links may point into the checkout, so pulling or switching the
active checkout can activate changed files immediately. Use a permanent separate
checkout for the new layout and keep the old checkout until migration succeeds.

## Review and install

Before activating this version:

1. Record the active checkout revision, uncommitted work and literal targets for
   each existing dotfile link. Keep a private backup outside the repository of
   the checkout, local overrides, credentials and any other files involved.
2. Review all Stow packages and the Git history for secrets, identity, internal
   paths and network details. Enable GitHub push protection. Rotate any real
   credential found in history before cleaning the history.
3. Clone or prepare this revision in a permanent checkout. Run `./install.sh
   --dry-run`; review every link and conflict. The default is `zsh git vim tmux`.
   Add `--ssh` only after reviewing the public SSH defaults and private local
   include.
4. If conflicts are expected, retain the preview and run `./install.sh
   --backup` only after reviewing the private backup location. The installer
   preserves displaced files, directories and symlinks under
   `~/.dotfiles_backups`, then Stow creates leaf links with `--no-folding`.
5. Run `./install.sh deps` only when ready to install missing dependencies.
   `./install.sh update` is a separate explicit upgrade. Neither is needed just
   to link configuration.
6. In new processes, check shell startup, Git identity, SSH configuration, Vim
   editing and tmux. Keep the old checkout and private backups until these checks
   succeed.

Never run installation or restore tests against the real HOME. The test suite
uses temporary HOME directories and command substitutes.

## Transitional files

The old source paths and repository snapshot script remain during this first
phase so current HOME links do not become dangling before the owner performs the
device migration. `new-script` and `script-template` are no longer installed by
the new setup. If `set-wifi-dns` is still needed, copy it to `~/.local/bin/` and
provide that Mac's network values privately. Once the owner confirms migration,
a follow-up change can delete the obsolete source paths, scripts and `backup.sh`.
Conflict backups for files displaced by Stow remain part of the installer.

## Rollback

For each changed destination, verify that it is still the Stow-created symlink.
Remove only that link, then restore the saved object from its matching relative
path under the printed private backup directory. For paths that were absent
before installation, remove only the new link. A saved symlink records its link
text; separately preserve external targets whose contents matter.

Git restores committed repository contents. It cannot roll back local edits,
package updates, private files or data behind links. Keep the old checkout and a
separate private/system backup until the new configuration is verified.

## References

[GNU Stow manual](https://www.gnu.org/software/stow/manual/stow.html)
[Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile)
[Git ignore documentation](https://git-scm.com/docs/gitignore)
[GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection)
