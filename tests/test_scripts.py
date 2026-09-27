import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Scripts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dotfiles-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.repo = self.base / 'checkout with spaces'
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        self.home = self.base / 'home'
        self.home.mkdir()
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), ZDOTDIR=str(self.home),
                        PATH=f'{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin',
                        GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                        EDITOR='', LC_ALL='C')
        self.env.pop('ZSH_CUSTOM', None)
        for cmd in ('curl', 'brew', 'sudo', 'chsh', 'networksetup', 'osascript'):
            self.stub(cmd, 'exit 91')

    def stub(self, name, body):
        p = self.bin / name
        p.write_text('#!/bin/sh\n' + body + '\n')
        p.chmod(0o755)

    def run_script(self, name, *args, input=''):
        return subprocess.run(['/bin/zsh', '-f', str(self.repo / name), *args],
                              env=self.env, cwd=self.repo, input=input, text=True,
                              capture_output=True, timeout=20)

    def test_install_help_has_no_side_effects(self):
        result = self.run_script('install.sh', '--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Usage:', result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])

    def prepare_install(self):
        for cmd in ('git', 'vim', 'tmux', 'ruff', 'shellcheck', 'clang', 'markdownlint', 'prettier'):
            self.stub(cmd, 'exit 0')
        (self.home / '.vim/autoload').mkdir(parents=True)
        (self.home / '.vim/autoload/plug.vim').touch()
        for plugin in ('zsh-autosuggestions', 'zsh-syntax-highlighting'):
            (self.home / '.oh-my-zsh/custom/plugins' / plugin).mkdir(parents=True)
        (self.home / '.gitconfig.local').write_text('existing identity')
        (self.home / '.ssh').mkdir()
        (self.home / '.ssh/config.local').write_text('existing hosts')

    def test_install_preserves_files_and_is_repeatable(self):
        self.prepare_install()
        (self.home / '.vimrc').write_text('old vim')
        (self.home / '.tmux.conf').symlink_to(self.home / 'missing')
        before = (self.repo / 'zsh/zshrc').read_bytes()
        for _ in range(2):
            result = self.run_script('install.sh')
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / '.gitconfig.local').read_text(), 'existing identity')
        self.assertEqual((self.home / '.ssh/config.local').read_text(), 'existing hosts')
        self.assertEqual((self.home / '.vimrc').resolve(), self.repo / 'vim/vimrc')
        self.assertEqual((self.home / '.local/bin/new-script').resolve(), self.repo / 'scripts/new-script.sh')
        self.assertTrue(any(p.read_text() == 'old vim' for p in (self.home / '.dotfiles_backups').glob('*/.vimrc')))
        self.assertFalse((self.repo / 'zshrc').exists())
        self.assertEqual((self.repo / 'zsh/zshrc').read_bytes(), before)

    def test_install_rejects_linux_before_changes(self):
        self.stub('uname', 'echo Linux')
        result = self.run_script('install.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('macOS', result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_install_stops_on_dependency_failure(self):
        result = self.run_script('install.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / '.gitconfig').exists())
        self.assertFalse((self.home / '.vim').exists())

    def test_generator_uses_checkout_and_literal_description(self):
        description = 'pipes | ampersands & quotes " and backslash \\'
        result = self.run_script('scripts/new-script.sh', 'example', description)
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.repo / 'scripts/example.sh'
        self.assertIn('# Description: ' + description, target.read_text())
        self.assertEqual((self.home / '.local/bin/example').resolve(), target)
        again = self.run_script('scripts/new-script.sh', 'example')
        self.assertNotEqual(again.returncode, 0)
        self.assertIn(description, target.read_text())
        empty = self.run_script('scripts/new-script.sh', 'empty', '')
        self.assertEqual(empty.returncode, 0, empty.stderr)
        self.assertIn('# Description: \n', (self.repo / 'scripts/empty.sh').read_text())

    def test_generator_rejects_dangling_target(self):
        (self.repo / 'scripts/example.sh').symlink_to(self.base / 'missing')
        result = self.run_script('scripts/new-script.sh', 'example')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.repo / 'scripts/example.sh').is_symlink())

    def snapshot(self):
        result = self.run_script('backup.sh', '-b')
        self.assertEqual(result.returncode, 0, result.stderr)
        return next((self.home / 'dotfiles_backup').iterdir())

    def test_restore_preserves_git_extra_files_and_previous_contents(self):
        (self.repo / '.git').mkdir()
        (self.repo / '.git/marker').write_text('git metadata')
        snapshot = self.snapshot()
        (self.repo / 'README.md').write_text('new contents')
        (self.repo / 'extra').write_text('keep')
        result = self.run_script('backup.sh', '-r', input=snapshot.name + '\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / '.git/marker').read_text(), 'git metadata')
        self.assertEqual((self.repo / 'extra').read_text(), 'keep')
        self.assertEqual((self.repo / 'README.md').read_bytes(), (snapshot / 'README.md').read_bytes())
        self.assertTrue(any(p.read_text() == 'new contents' for p in (self.home / 'dotfiles_backup').glob('pre-recovery-*/README.md')))

    def test_restore_rejects_escape_and_backup_failure(self):
        snapshot = self.snapshot()
        (self.repo / 'README.md').write_text('keep me')
        result = self.run_script('backup.sh', '-r', input='../outside\n')
        self.assertNotEqual(result.returncode, 0)
        self.stub('rsync', 'exit 73')
        result = self.run_script('backup.sh', '-r', input=snapshot.name + '\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.repo / 'README.md').read_text(), 'keep me')

    def git(self, *args):
        return subprocess.run(['/usr/bin/git', *args], cwd=self.repo, env=self.env,
                              check=True, text=True, capture_output=True)

    def test_prepare_message_preserves_text_and_comments(self):
        self.git('init')
        self.git('checkout', '-b', 'feature-42-example')
        message = self.base / 'message'
        message.write_text('Useful title\n\nDetails\n# comment\n')
        result = self.run_script('git/git-template/hooks/prepare-commit-msg', str(message))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Useful title', message.read_text())
        self.assertIn('Details', message.read_text())
        self.assertIn('# comment', message.read_text())
        self.assertIn('[feature-42-example]', message.read_text())

    def test_pre_commit_handles_spaced_and_newline_names(self):
        self.git('init')
        for name in ('file with spaces.txt', 'line\nbreak.txt'):
            (self.repo / name).write_text('trailing   \n')
        self.git('add', '.')
        result = self.run_script('git/git-template/hooks/pre-commit')
        self.assertNotEqual(result.returncode, 0)
        for name in ('file with spaces.txt', 'line\nbreak.txt'):
            self.assertEqual((self.repo / name).read_text(), 'trailing\n')

    def test_notification_passes_message_as_data(self):
        self.stub('git', "printf '%s\\n' 'A \"quote\" and backslash \\\\'")
        self.stub('osascript', 'printf "%s\\n" "$@" > "$HOME/notification-args"; cat > "$HOME/notification-source"')
        result = self.run_script('git/git-template/hooks/post-commit')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('A "quote"', (self.home / 'notification-args').read_text())
        self.assertNotIn('A "quote"', (self.home / 'notification-source').read_text())
        self.assertIn('item 1 of argv', (self.home / 'notification-source').read_text())

    def test_install_creates_identity_and_ssh_directory(self):
        self.prepare_install()
        (self.home / '.gitconfig.local').unlink()
        shutil.rmtree(self.home / '.ssh')
        result = self.run_script('install.sh', input='Test User\ntest@example.invalid\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Test User', (self.home / '.gitconfig.local').read_text())
        self.assertTrue((self.home / '.ssh/config').is_symlink())
        self.assertEqual((self.home / '.gitconfig.local').stat().st_mode & 0o777, 0o600)

    def test_version_and_unknown_option_do_not_install(self):
        self.assertEqual(self.run_script('install.sh', '--version').returncode, 0)
        self.assertNotEqual(self.run_script('install.sh', '--unknown').returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_restore_rejects_symlink_outside_backup_root(self):
        snapshot = self.snapshot()
        (snapshot.parent / 'outside').symlink_to(self.repo, target_is_directory=True)
        result = self.run_script('backup.sh', '-r', input='outside\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(list(snapshot.parent.glob('pre-recovery-*')))


if __name__ == '__main__':
    unittest.main()
