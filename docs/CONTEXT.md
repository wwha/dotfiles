# Personal macOS configuration

Shared configuration is maintained in this repository and installed on personal Macs.

## Language

**Shared configuration**: Versioned shell, editor, and tool settings intended to be reused across the owner's Macs.

**Local override**: Machine-specific settings, identity or secrets kept outside version control.

**Installation**: Linking shared configuration into a user's home directory while preserving local overrides and displaced configuration.

**Dependency setup**: Explicit preparation of the packages and plugins used by shared configuration, separate from installation. Installation checks all Brewfile packages before
changing HOME paths; missing dependencies require explicit dependency setup.
A dry-run previews links without this check.

**Conflict backup**: The original file, directory or symlink displaced by installation, retained for per-file rollback. A saved symlink does not include its target's contents.

**Restore**: Returning a displaced file, directory or symlink from its per-file installer backup.

**Activation**: The point when a Mac starts reading a changed shared configuration, including changes reached through existing symlinks.
