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
                        PATH=f'{self.bin}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
                        GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                        EDITOR='', LC_ALL='C')
        self.env.pop('ZSH_CUSTOM', None)
        for cmd in ('curl', 'brew', 'sudo', 'chsh', 'networksetup', 'osascript'):
            self.stub(cmd, 'exit 91')
        self.stub_stow()

    def stub(self, name, body):
        p = self.bin / name
        p.write_text('#!/bin/sh\n' + body + '\n')
        p.chmod(0o755)

    def stub_stow(self):
        p = self.bin / 'stow'
        p.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
args = sys.argv[1:]
source = pathlib.Path(next(x[6:] for x in args if x.startswith('--dir=')))
target = pathlib.Path(next(x[9:] for x in args if x.startswith('--target=')))
simulate = '--simulate' in args
packages = [x for x in args if not x.startswith('-')]
conflict = False
for package in packages:
    root = source / package
    for item in root.rglob('*'):
        if not item.is_file():
            continue
        dest = target / item.relative_to(root)
        if dest.is_symlink() and dest.resolve() == item.resolve():
            continue
        if dest.exists() or dest.is_symlink():
            print('CONFLICT: ' + str(dest), file=sys.stderr)
            conflict = True
            continue
        if simulate:
            print('LINK: ' + str(dest) + ' -> ' + str(item))
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.symlink_to(item)
sys.exit(1 if conflict else 0)
''')
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
        for cmd in ('git', 'vim', 'tmux', 'ruff', 'clang', 'markdownlint', 'prettier'):
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
        before = (self.repo / 'stow/zsh/.zshrc').read_bytes()
        result = self.run_script('install.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Conflicts found', result.stderr)
        self.assertFalse((self.home / '.gitconfig').exists())
        for _ in range(2):
            result = self.run_script('install.sh', '--backup')
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / '.gitconfig.local').read_text(), 'existing identity')
        self.assertEqual((self.home / '.ssh/config.local').read_text(), 'existing hosts')
        self.assertEqual((self.home / '.vimrc').resolve(), self.repo / 'stow/vim/.vimrc')
        self.assertFalse((self.home / '.local/bin/new-script').exists())
        self.assertTrue(any(p.read_text() == 'old vim' for p in (self.home / '.dotfiles_backups').glob('*/.vimrc')))
        self.assertEqual((self.repo / 'stow/zsh/.zshrc').read_bytes(), before)

    def test_install_rejects_linux_before_changes(self):
        self.stub('uname', 'echo Linux')
        result = self.run_script('install.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('macOS', result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_install_is_offline_and_does_not_distribute_legacy_tools(self):
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / '.gitconfig').is_symlink())
        self.assertFalse((self.home / '.ssh').exists())
        self.assertFalse((self.home / '.local/bin').exists())
        self.assertFalse((self.home / '.git-template/hooks').exists())
        self.assertFalse((self.home / '.vim').exists())
        self.assertFalse((self.home / '.gitconfig.local').exists())

    def test_real_stow_creates_leaf_links_without_folding_directories(self):
        stow = shutil.which('stow', path='/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin')
        if not stow:
            self.skipTest('GNU Stow is not installed')
        (self.bin / 'stow').unlink()
        result = self.run_script('install.sh', '--ssh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / '.zshrc').resolve(), self.repo / 'stow/zsh/.zshrc')
        self.assertTrue((self.home / '.config/dotfiles/zsh/rime-ice-update.zsh').is_symlink())
        self.assertFalse((self.home / '.config').is_symlink())
        self.assertFalse((self.home / '.git-template').is_symlink())
        self.assertTrue((self.home / '.ssh/config').is_symlink())

    def test_install_completes_partial_template_without_replacing_custom_files(self):
        template = self.home / '.git-template'
        (template / 'hooks').mkdir(parents=True)
        (template / 'hooks/pre-commit').write_text('private hook')
        (template / 'gitignore').write_text('private ignore')
        result = self.run_script('install.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Conflicts found', result.stderr)
        result = self.run_script('install.sh', '--backup')
        self.assertEqual(result.returncode, 0, result.stderr)
        saved_ignore = next((self.home / '.dotfiles_backups').glob('*/.git-template/gitignore'))
        self.assertEqual(saved_ignore.read_text(), 'private ignore')
        self.assertEqual((template / 'hooks/pre-commit').read_text(), 'private hook')
        self.assertEqual((template / 'commit-template').resolve(),
                         self.repo / 'stow/git/.git-template/commit-template')

    def test_dry_run_preserves_conflicts_and_creates_nothing(self):
        (self.home / '.vimrc').write_text('original')
        (self.home / '.tmux.conf').symlink_to('missing')
        before = sorted(p.name for p in self.home.iterdir())
        result = self.run_script('install.sh', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Would back up:', result.stdout)
        self.assertIn('Would link:', result.stdout)
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), before)
        self.assertEqual((self.home / '.vimrc').read_text(), 'original')
        self.assertEqual(os.readlink(self.home / '.tmux.conf'), 'missing')
        result = self.run_script('install.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / '.zshrc').exists())
        result = self.run_script('install.sh', '--backup')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_install_backs_up_links_and_directories_without_following(self):
        (self.home / '.vimrc').symlink_to('missing')
        (self.home / '.tmux.conf').mkdir()
        (self.home / '.tmux.conf/marker').write_text('keep')
        target = self.base / 'external'
        target.write_text('external')
        (self.home / '.zshrc').symlink_to(target)
        result = self.run_script('install.sh', '--backup')
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = self.home / '.dotfiles_backups'
        saved_link = next(p / '.vimrc' for p in backups.iterdir() if (p / '.vimrc').is_symlink())
        self.assertEqual(os.readlink(saved_link), 'missing')
        saved_directory = next(backups.glob('*/.tmux.conf'))
        self.assertEqual((saved_directory / 'marker').read_text(), 'keep')
        self.assertEqual(os.readlink(next(backups.glob('*/.zshrc'))), str(target))
        self.assertEqual(target.read_text(), 'external')
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o700 for p in backups.iterdir()))
        # Demonstrate rollback: replace the installed link with the saved directory.
        (self.home / '.tmux.conf').unlink()
        saved_directory.rename(self.home / '.tmux.conf')
        self.assertEqual((self.home / '.tmux.conf/marker').read_text(), 'keep')

    def test_existing_install_keeps_legacy_links_and_private_files(self):
        # Reproduce the old installer's public layout, including its template symlink.
        for name, source in {'.zshrc': 'stow/zsh/.zshrc', '.vimrc': 'stow/vim/.vimrc',
                             '.tmux.conf': 'stow/tmux/.tmux.conf',
                             '.gitconfig': 'stow/git/.gitconfig'}.items():
            (self.home / name).symlink_to(self.repo / source)
        (self.home / '.git-template').symlink_to(self.repo / 'git/git-template')
        (self.home / '.ssh').mkdir()
        (self.home / '.ssh/config').symlink_to(self.repo / 'stow/ssh/.ssh/config')
        (self.home / '.local/bin').mkdir(parents=True)
        for name in ('new-script', 'script-template', 'set-wifi-dns'):
            (self.home / '.local/bin' / name).symlink_to(self.repo / f'scripts/{name}.sh')
        locals = ('.gitconfig.local', '.ssh/config.local', '.api_keys')
        for name in locals:
            (self.home / name).write_text('private ' + name)
            (self.home / name).chmod(0o600)
        (self.repo / 'stow/ssh/.ssh/config.local').write_text('must not replace HOME local')
        result = self.run_script('install.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Conflicts found', result.stderr)
        result = self.run_script('install.sh', '--backup')
        self.assertEqual(result.returncode, 0, result.stderr)
        links = {p: (os.readlink(p), p.lstat().st_mtime_ns)
                 for p in self.home.rglob('*') if p.is_symlink() and p.name != '.git-template'}
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        for p, before in links.items():
            self.assertEqual((os.readlink(p), p.lstat().st_mtime_ns), before)
            self.assertTrue(p.exists())
        for name in locals:
            self.assertEqual((self.home / name).read_text(), 'private ' + name)
            self.assertEqual((self.home / name).stat().st_mode & 0o777, 0o600)
        self.assertTrue((self.home / '.dotfiles_backups').is_dir())
        saved_template = next((self.home / '.dotfiles_backups').glob('*/.git-template'))
        self.assertTrue(saved_template.is_symlink())
        for name in ('script-template', 'set-wifi-dns'):
            result = self.run_script(str(self.home / '.local/bin' / name), '--help')
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_script(str(self.home / '.local/bin/new-script'), 'migration-probe')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_install_ssh_is_opt_in_and_refuses_symlinked_parent(self):
        (self.home / '.ssh').mkdir()
        (self.home / '.ssh/config').write_text('private ssh config')
        result = self.run_script('install.sh', '--ssh')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.home / '.ssh/config').read_text(), 'private ssh config')
        self.assertFalse((self.home / '.zshrc').exists())
        (self.home / '.ssh/config').unlink()
        (self.home / '.ssh').rmdir()
        target = self.base / 'ssh-target'
        target.mkdir()
        (self.home / '.ssh').symlink_to(target, target_is_directory=True)
        result = self.run_script('install.sh', '--ssh')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / '.gitconfig').exists())

    def test_install_rejects_insecure_backup_directory_before_linking(self):
        backup_root = self.home / '.dotfiles_backups'
        backup_root.mkdir(mode=0o755)
        backup_root.chmod(0o755)
        (self.home / '.vimrc').write_text('original')
        result = self.run_script('install.sh', '--backup')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / '.gitconfig').exists())
        self.assertEqual((self.home / '.vimrc').read_text(), 'original')

    def test_dependency_failure_does_not_link_configuration(self):
        result = self.run_script('install.sh', 'deps')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_update_is_explicit_and_does_not_link_configuration(self):
        self.stub('brew', 'printf "%s\\n" "$*" >> "$HOME/brew-args"')
        result = self.run_script('install.sh', 'update')
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.home / 'brew-args').read_text()
        self.assertIn('update', args)
        self.assertIn('bundle upgrade --file=' + str(self.repo / 'Brewfile'), args)
        self.assertFalse((self.home / '.zshrc').exists())

    def test_git_local_override_and_installed_ignore(self):
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.env.pop('GIT_CONFIG_GLOBAL')
        (self.home / '.gitconfig.local').write_text('[core]\n editor = local-editor\n')
        self.assertEqual(self.git('config', '--get', 'core.editor').stdout.strip(), 'local-editor')
        self.assertEqual(self.git('config', '--bool', '--get', 'user.useConfigOnly').stdout.strip(), 'true')
        self.git('init', '--template=')
        ignored = self.git('check-ignore', '.DS_Store').stdout.strip()
        self.assertEqual(ignored, '.DS_Store')
        self.assertEqual(self.git('config', '--path', '--get', 'core.excludesfile').stdout.strip(),
                         str(self.home / '.git-template/gitignore'))
        hook = self.repo / '.git/hooks/commit-msg'
        hook.parent.mkdir(exist_ok=True)
        hook.write_text('#!/bin/sh\nexit 23\n')
        hook.chmod(0o755)
        result = subprocess.run(
            ['/usr/bin/git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
             'commit', '--allow-empty', '-m', 'fixture'],
            cwd=self.repo, env=self.env, text=True, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / '.git-hooks').exists())

    def test_repository_ignore_protects_secrets_without_hiding_project_files(self):
        self.git('init')
        for name in ('.api_keys', '.env.production', 'id_ed25519', 'private.pem'):
            (self.repo / name).write_text('secret')
            self.assertTrue(self.git('check-ignore', '--no-index', name).stdout.strip(), name)
        for name in ('.env.example', 'schema.sql', 'vendor/library.c'):
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('example or project file')
            result = subprocess.run(['/usr/bin/git', 'check-ignore', '--no-index', name],
                                    cwd=self.repo, env=self.env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1, name)

    def test_vim_without_plugins_does_not_load_local_override(self):
        (self.home / '.vimrc.local').write_text('set tabstop=7\n')
        script = self.base / 'probe.vim'
        output = self.base / 'vim-result'
        script.write_text("call writefile([string(&tabstop), string(g:ale_linters['zsh']), string(g:ale_linters['sh'])], '" +
                          str(output) + "')\nqa!\n")
        result = subprocess.run(['/usr/bin/vim', '-N', '-u', str(self.repo / 'stow/vim/.vimrc'),
                                 '-i', 'NONE', '-n', '-es', '-S', str(script)],
                                env=self.env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text(), '4\n[]\n[]\n')

    def test_vim_preserves_recovery_and_disables_automatic_edits_by_default(self):
        output = self.base / 'vim-options'
        script = self.base / 'probe.vim'
        script.write_text("call writefile([string(&swapfile), string(&backup), string(g:ale_fix_on_save), string(exists('#osc52#TextYankPost')), string(exists('#file_templates#BufNewFile'))], '" + str(output) + "')\nqa!\n")
        result = subprocess.run(['/usr/bin/vim', '-N', '-u', str(self.repo / 'stow/vim/.vimrc'),
                                 '-i', 'NONE', '-n', '-es', '-S', str(script)],
                                env=self.env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = output.read_text().splitlines()
        self.assertEqual(values[:3], ['1', '0', '0'])
        self.assertEqual(values[3:], ['1', '0'])

    def test_vim_buffer_close_does_not_discard_modified_content(self):
        target = self.base / 'unsaved.txt'
        target.write_text('saved\n')
        output = self.base / 'vim-buffer'
        script = self.base / 'probe.vim'
        script.write_text("execute 'edit ' . fnameescape('" + str(target) + "')\n"
                          "let b = bufnr('%')\ncall setline(1, 'unsaved')\n"
                          "try\nBclose\ncatch\nendtry\n"
                          "call writefile([string(bufexists(b)), getbufline(b, 1)[0], string(getbufvar(b, '&modified'))], '" + str(output) + "')\nqa!\n")
        result = subprocess.run(['/usr/bin/vim', '-N', '-u', str(self.repo / 'stow/vim/.vimrc'),
                                 '-i', 'NONE', '-n', '-es', '-S', str(script)],
                                env=self.env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text().splitlines(), ['1', 'unsaved', '1'])

    def test_zsh_preserves_initializers_without_local_override(self):
        for name, body in {
            '.oh-my-zsh/oh-my-zsh.sh': 'export OMZ_LOADED=yes',
            'miniconda3/bin/conda': '#!/bin/sh\nprintf "export CONDA_LOADED=yes\\n"',
            '.nvm/nvm.sh': 'export NVM_LOADED=yes',
            '.api_keys': 'export TEST_API_KEY=fixture',
            '.zshrc.local': 'export HOMEBREW_NO_ANALYTICS=local',
        }.items():
            p = self.home / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body + '\n')
            p.chmod(0o700)
        env = dict(self.env, TERM_PROGRAM='test', TMUX='', SSH_CONNECTION='')
        result = subprocess.run(['/bin/zsh', '-f', '-c',
                                 'source "$1"; print -r -- "$OMZ_LOADED $CONDA_LOADED $NVM_LOADED $TEST_API_KEY $HOMEBREW_NO_ANALYTICS"',
                                 'probe', str(self.repo / 'stow/zsh/.zshrc')],
                                env=env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'yes yes yes  1')
        self.assertEqual(result.stderr, '')

    def test_shared_ssh_helpers_keep_preferences_and_reject_shell_metacharacters(self):
        env = dict(self.env, TERM_PROGRAM='test', TMUX='', SSH_CONNECTION='')
        probe = ('ssh() { print -rl -- "$@" >> "$HOME/ssh-args"; }; '
                 'source "$1"; ssht host.example safe_session; sshp host.example; '
                 'sshp "host;touch"; print -r -- done')
        result = subprocess.run(['/bin/zsh', '-f', '-c', probe, 'probe',
                                 str(self.repo / 'stow/zsh/.zshrc')],
                                env=env, cwd=self.repo, text=True,
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'ssh-args').read_text().splitlines(), [
            '-t', 'host.example', "exec zsh -l -c 'tmux new-session -s safe_session'",
            'host.example'])
        self.assertIn('unsupported characters', result.stderr)

    def test_bun_is_not_loaded_from_local_override(self):
        (self.home / '.bun').mkdir()
        (self.home / '.bun/_bun').write_text('export BUN_LOADED=yes\n')
        env = dict(self.env, TERM_PROGRAM='test', TMUX='', SSH_CONNECTION='')
        for name in ('BUN_INSTALL', 'BUN_LOADED'):
            env.pop(name, None)
        probe = 'source "$1"; print -r -- "${BUN_INSTALL:-absent}|${BUN_LOADED:-absent}|${path[(Ie)$HOME/.bun/bin]}"'
        def load():
            return subprocess.run(['/bin/zsh', '-f', '-c', probe, 'probe', str(self.repo / 'stow/zsh/.zshrc')],
                                  env=env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        result = load()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'absent|absent|0')
        (self.home / '.zshrc.local').write_text(
            'export BUN_INSTALL="$HOME/.bun"\n'
            'export PATH="$BUN_INSTALL/bin:$PATH"\n'
            '[ -s "$BUN_INSTALL/_bun" ] && source "$BUN_INSTALL/_bun"\n')
        result = load()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'absent|absent|0')

    def test_shared_zsh_starts_tmux_in_local_terminal_sessions(self):
        env = dict(self.env, TERM_PROGRAM='Apple_Terminal', TMUX='', SSH_CONNECTION='')
        self.stub('tmux', 'touch "$HOME/tmux-called"; exit 91')
        result = subprocess.run(['/bin/zsh', '-f', '-c', 'tmux() { : > "$HOME/tmux-called"; return 1; }; source "$1"', 'probe', str(self.repo / 'stow/zsh/.zshrc')],
                                env=env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / 'tmux-called').exists())

    def test_network_script_requires_explicit_values_and_validates_before_sudo(self):
        self.stub('sudo', 'printf "%s\\n" "$@" >> "$HOME/sudo-args"')
        result = self.run_script('scripts/set-wifi-dns.sh', 'manual', 'Wi-Fi', '10.1.2.3',
                                 '255.255.255.0', '10.1.2.1', '1.1.1.1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('10.1.2.3', (self.home / 'sudo-args').read_text())
        (self.home / 'sudo-args').unlink()
        result = self.run_script('scripts/set-wifi-dns.sh', 'manual', 'Wi-Fi', '999.1.2.3',
                                 '255.255.255.0', '10.1.2.1', '1.1.1.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / 'sudo-args').exists())
        result = self.run_script('scripts/set-wifi-dns.sh', 'manual')
        self.assertNotEqual(result.returncode, 0)

    def test_tmux_ignores_local_override_and_limits_clipboard_access(self):
        tmux = shutil.which('tmux')
        if not tmux:
            tmux = next((p for p in ('/opt/homebrew/bin/tmux', '/usr/local/bin/tmux')
                         if Path(p).is_file()), None)
        if not tmux:
            self.skipTest('tmux is not installed')
        socket_dir = tempfile.TemporaryDirectory(prefix='df-tmux-', dir='/tmp')
        self.addCleanup(socket_dir.cleanup)
        socket = str(Path(socket_dir.name) / 'socket')
        env = dict(self.env)
        env.pop('TMUX', None)
        def tmux_run(*args):
            return subprocess.run([tmux, '-S', socket, *args], env=env, cwd=self.repo,
                                  text=True, capture_output=True, timeout=10)
        self.addCleanup(lambda: tmux_run('kill-server'))
        started = tmux_run('-f', '/dev/null', 'new-session', '-d', '-s', 'test', '/bin/sleep 60')
        if 'Operation not permitted' in started.stderr:
            self.skipTest('sandbox does not permit Unix socket creation')
        self.assertEqual(started.returncode, 0, started.stderr)
        # tmux may report socket creation failure on stderr while exiting with 0.
        self.assertEqual(started.stderr, '', 'Isolated tmux server failed: ' + started.stderr)
        (self.home / '.tmux.conf.local').write_text('set -g display-panes-time 3456\n')
        result = tmux_run('source-file', str(self.repo / 'stow/tmux/.tmux.conf'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(tmux_run('show-options', '-gv', 'display-panes-time').stdout.strip(), '1500')
        command = tmux_run('show-options', '-sv', 'copy-command').stdout.strip()
        self.assertTrue(command)
        self.assertEqual(tmux_run('show-options', '-sv', 'set-clipboard').stdout.strip(), 'external')
        self.stub('pbcopy', 'cat > "$HOME/copied"')
        self.stub('xclip', 'touch "$HOME/unexpected-xclip"; exit 91')
        copied = subprocess.run(['/bin/sh', '-c', command], input='clipboard text',
                                env=env, text=True, capture_output=True, timeout=10)
        self.assertEqual(copied.returncode, 0, copied.stderr)
        self.assertEqual((self.home / 'copied').read_text(), 'clipboard text')
        self.assertFalse((self.home / 'unexpected-xclip').exists())

    def test_dependencies_are_explicit_and_fetch_latest_plugins_only_on_request(self):
        (self.home / '.zshrc').write_text('keep shell config')
        self.stub('brew', 'printf "%s\\n" "$@" >> "$HOME/brew-args"')
        self.stub('curl', 'printf "%s\\n" "$*" > "$HOME/curl-args"; while [ "$#" -gt 0 ]; do if [ "$1" = -o ]; then shift; : > "$1"; fi; shift; done')
        self.stub('git', 'mkdir -p "$4/tools"; : > "$4/oh-my-zsh.sh"')
        self.stub('vim', 'printf "%s\\n" "$@" > "$HOME/vim-args"')
        result = self.run_script('install.sh', 'deps')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / '.zshrc').read_text(), 'keep shell config')
        self.assertTrue((self.home / '.vim/autoload/plug.vim').is_file())
        self.assertTrue((self.home / '.oh-my-zsh/oh-my-zsh.sh').is_file())
        self.assertIn('PlugInstall', (self.home / 'vim-args').read_text())
        self.assertIn('raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim',
                      (self.home / 'curl-args').read_text())
        self.assertIn('--file=' + str(self.repo / 'Brewfile'), (self.home / 'brew-args').read_text())
        self.assertFalse((self.home / '.gitconfig').exists())

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
