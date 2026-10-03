import os
import pty
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import time
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
        hook = self.home / '.git-template/hooks/pre-commit'
        self.assertTrue(hook.is_symlink())
        self.assertEqual(hook.resolve(), self.repo / 'stow/git/.git-template/hooks/pre-commit')
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
        self.assertFalse((self.home / '.config/dotfiles/zsh/rime-ice-update.zsh').is_symlink())
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
        self.assertEqual((template / 'hooks/pre-commit.local').read_text(), 'private hook')
        self.assertEqual((template / 'hooks/pre-commit').resolve(),
                         self.repo / 'stow/git/.git-template/hooks/pre-commit')
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

    def test_template_pre_commit_scans_then_runs_repository_checks(self):
        self.stub('gitleaks', 'printf "%s\\n" "$*" >> "$HOME/hook-args"\nif [ -e "$PWD/block-secret" ]; then exit 1; fi')
        self.stub('pre-commit', 'printf "%s\\n" "$*" >> "$HOME/hook-args"')
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        local_hook = self.home / '.git-template/hooks/pre-commit.local'
        local_hook.write_text('#!/bin/sh\nexit 17\n')
        local_hook.chmod(0o644)
        self.git('init', '--template=' + str(self.home / '.git-template'))
        result = subprocess.run(
            ['/usr/bin/git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
             'commit', '--allow-empty', '-m', 'fixture'],
            cwd=self.repo, env=self.env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'hook-args').read_text().splitlines(),
                         ['git --pre-commit --staged --redact', 'run --hook-stage pre-commit'])
        copied_local_hook = self.repo / '.git/hooks/pre-commit.local'
        self.assertFalse(copied_local_hook.stat().st_mode & 0o111)
        copied_local_hook.chmod(0o755)
        result = subprocess.run(
            ['/usr/bin/git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
             'commit', '--allow-empty', '-m', 'disabled local hook stays skipped'],
            cwd=self.repo, env=self.env, text=True, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        (self.repo / 'block-secret').write_text('fixture')
        self.git('add', 'block-secret')
        result = subprocess.run(
            ['/usr/bin/git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
             'commit', '-m', 'blocked'],
            cwd=self.repo, env=self.env, text=True, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)

    def test_git_defaults_reject_divergent_pull_and_reuse_unstaged_resolution(self):
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.env.pop('GIT_CONFIG_GLOBAL')
        self.git('init', '--template=')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        file = self.repo / 'conflict.txt'
        file.write_text('base\n')
        self.git('add', 'conflict.txt')
        self.git('commit', '-m', 'base')
        other = self.base / 'other'
        self.git('clone', '--template=', str(self.repo), str(other))
        subprocess.run(['/usr/bin/git', '-C', str(other), 'config', 'user.name', 'Fixture'],
                       env=self.env, check=True, capture_output=True)
        subprocess.run(['/usr/bin/git', '-C', str(other), 'config', 'user.email', 'fixture@example.invalid'],
                       env=self.env, check=True, capture_output=True)
        (other / 'conflict.txt').write_text('remote\n')
        for args in (['add', 'conflict.txt'], ['commit', '-m', 'remote']):
            subprocess.run(['/usr/bin/git', '-C', str(other), *args], env=self.env,
                           check=True, capture_output=True)
        self.git('remote', 'add', 'origin', str(other))
        file.write_text('local\n')
        self.git('add', 'conflict.txt')
        self.git('commit', '-m', 'local')
        before = self.git('rev-parse', 'HEAD').stdout.strip()
        pull = subprocess.run(['/usr/bin/git', 'pull', 'origin', 'main'],
                              cwd=self.repo, env=self.env, text=True, capture_output=True)
        self.assertNotEqual(pull.returncode, 0)
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), before)
        merge = subprocess.run(['/usr/bin/git', 'merge', 'origin/main'],
                               cwd=self.repo, env=self.env, text=True, capture_output=True)
        self.assertNotEqual(merge.returncode, 0)
        self.assertIn('|||||||', file.read_text())
        file.write_text('resolved\n')
        self.git('add', 'conflict.txt')
        self.git('commit', '-m', 'resolve')
        self.git('reset', '--hard', before)
        merge = subprocess.run(['/usr/bin/git', 'merge', 'origin/main'],
                               cwd=self.repo, env=self.env, text=True, capture_output=True)
        self.assertNotEqual(merge.returncode, 0)
        self.assertEqual(file.read_text(), 'resolved\n')
        self.assertTrue(self.git('ls-files', '-u').stdout)
        self.assertEqual(self.git('config', '--get', 'core.pager').stdout.strip(), 'delta')
        self.assertEqual(self.git('config', '--get', 'interactive.diffFilter').stdout.strip(),
                         'delta --color-only')
        self.assertEqual(self.git('config', '--get', 'alias.d').stdout.strip(), 'diff')
        (self.home / '.gitconfig.local').write_text('[core]\n pager = cat\n')
        self.assertEqual(self.git('config', '--get', 'core.pager').stdout.strip(), 'cat')

    def test_global_ignore_keeps_project_files_visible(self):
        (self.repo / '.gitignore').unlink()
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.env.pop('GIT_CONFIG_GLOBAL')
        self.git('init', '--template=')
        for name, expected in [('.DS_Store', 0), ('private.key', 0), ('id_ed25519', 0),
                               ('.env.production', 0), ('settings.local.json', 0),
                               ('build/source.c', 1), ('site/index.html', 1),
                               ('dist/asset.js', 1), ('library.zip', 1),
                               ('public.crt', 1), ('.vscode/settings.json', 1),
                               ('.env.example', 1)]:
            with self.subTest(name=name):
                probe = subprocess.run(['/usr/bin/git', 'check-ignore', '--no-index', name],
                                       cwd=self.repo, env=self.env, capture_output=True)
                self.assertEqual(probe.returncode, expected)

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

    def test_vim_preserves_recovery_and_enables_ale_save_fixes(self):
        output = self.base / 'vim-options'
        script = self.base / 'probe.vim'
        script.write_text("call writefile([string(&swapfile), string(&backup), string(g:ale_fix_on_save), string(exists('#osc52#TextYankPost')), string(exists('#file_templates#BufNewFile'))], '" + str(output) + "')\nqa!\n")
        result = subprocess.run(['/usr/bin/vim', '-N', '-u', str(self.repo / 'stow/vim/.vimrc'),
                                 '-i', 'NONE', '-n', '-es', '-S', str(script)],
                                env=self.env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = output.read_text().splitlines()
        self.assertEqual(values[:3], ['1', '0', '1'])
        self.assertEqual(values[3:], ['0', '0'])

    def test_vim_python_and_markdown_fix_on_save_and_mapping(self):
        plugin_home = Path(os.environ['HOME']) / '.vim'
        if not (plugin_home / 'plugged/ale/plugin/ale.vim').is_file():
            self.skipTest('ALE is not installed in the test host')
        if not shutil.which('ruff') or not shutil.which('prettier'):
            self.skipTest('Ruff and Prettier are required for fixer integration')
        (self.home / '.vim').mkdir()
        (self.home / '.vim/autoload').symlink_to(plugin_home / 'autoload')
        (self.home / '.vim/plugged').symlink_to(plugin_home / 'plugged')
        for ext, before, expected in (
                ('py', 'import os\nx=  1\n', 'x = 1\n'),
                ('py', 'while(True):\n    print("1")\n', 'while True:\n    print("1")\n'),
                ('md', '# Title\n\ntext   \n\n\n\n', '# Title\n\ntext\n'),
                ('md', '# Title\n\ntext   \nnext\n\n\n', '# Title\n\ntext  \nnext\n')):
            for action in ('write', 'call feedkeys(",af", "xt")'):
                with self.subTest(filetype=ext, action=action):
                    target = self.base / ('fix.' + ext)
                    target.write_text(before)
                    output = self.base / 'fixed'
                    script = self.base / 'fix.vim'
                    script.write_text('edit ' + str(target) + '\n' + action + '\nsleep 2\n'
                                      'call writefile(getline(1,"$"),"' + str(output) + '")\nqa!\n')
                    result = subprocess.run(
                        ['/usr/bin/vim', '-N', '-u', str(self.repo / 'stow/vim/.vimrc'),
                         '-i', 'NONE', '-n', '-es', '-S', str(script)],
                        env=self.env, cwd=self.repo, text=True, capture_output=True, timeout=15)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(output.read_text(), expected)
                    if action == 'write':
                        self.assertEqual(target.read_text(), expected)

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

    def test_vim_save_scope_and_buffer_close_mapping(self):
        target = self.base / 'plain.txt'
        target.write_text('keep spaces  \n')
        output = self.base / 'vim-scope'
        script = self.base / 'scope.vim'
        script.write_text(
            'edit ' + str(target) + '\nwrite\n'
            'vsplit\nenew\ncall feedkeys(",bd", "xt")\n'
            'call writefile([string(winnr("$")), string(tabpagenr("$")), '
            'string(has_key(g:ale_fixers, "*")), string(&textwidth), '
            'string(&termguicolors), maparg(",w", "n")], "' + str(output) + '")\nqa!\n')
        result = subprocess.run(['/usr/bin/vim', '-N', '-u', str(self.repo / 'stow/vim/.vimrc'),
                                 '-i', 'NONE', '-n', '-es', '-S', str(script)],
                                env=self.env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_text(), 'keep spaces  \n')
        self.assertEqual(output.read_text().splitlines(), ['2', '1', '0', '0', '1', ':w<CR>'])

    def test_zoxide_replaces_z_plugin_and_jumps_to_recorded_directory(self):
        if not shutil.which('zoxide', path=self.env['PATH']):
            self.skipTest('zoxide is not installed')
        omz = self.home / '.oh-my-zsh/oh-my-zsh.sh'
        omz.parent.mkdir()
        omz.write_text(':\n')
        target = self.base / 'project with spaces'
        target.mkdir()
        env = dict(self.env, _ZO_DATA_DIR=str(self.base / 'zoxide-data'))
        result = subprocess.run(
            ['/bin/zsh', '-f', '-c',
             'source "$1"; source "$1"; '
             '(( ${plugins[(Ie)z]} == 0 )) || exit 1; '
             'zoxide add -- "$2"; z project; print -r -- "$PWD"; '
             'typeset -a hooks; hooks=("${(@M)chpwd_functions:#__zoxide_hook}"); print -r -- "${#hooks}"',
             'probe', str(self.repo / 'stow/zsh/.zshrc'), str(target)],
            env=env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [str(target), '1'])

    def test_zsh_path_stays_unique_when_reloaded(self):
        omz = self.home / '.oh-my-zsh/oh-my-zsh.sh'
        omz.parent.mkdir()
        omz.write_text(':\n')
        inherited = '/opt/homebrew/bin:/usr/bin:/opt/homebrew/bin:/bin'
        result = subprocess.run(
            ['/bin/zsh', '-f', '-c', 'source "$1"; source "$1"; print -rl -- "${path[@]}"',
             'probe', str(self.repo / 'stow/zsh/.zshrc')],
            env=dict(self.env, PATH=inherited), cwd=self.repo,
            text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = result.stdout.splitlines()
        self.assertEqual(len(entries), len(set(entries)))
        for entry in ('/opt/homebrew/bin', '/opt/homebrew/opt/llvm/bin',
                      str(self.home / '.local/bin'), '/usr/bin', '/bin'):
            self.assertIn(entry, entries)

    def test_direnv_requires_approval_and_restores_project_environment(self):
        plugin = Path(os.environ['HOME']) / '.oh-my-zsh/plugins/direnv/direnv.plugin.zsh'
        if not plugin.is_file() or not shutil.which('direnv', path=self.env['PATH']):
            self.skipTest('direnv and its Oh My Zsh plugin are required')
        omz = self.home / '.oh-my-zsh/oh-my-zsh.sh'
        omz.parent.mkdir()
        omz.write_text('for plugin in $plugins; do\n'
                       '  [[ $plugin == direnv ]] && source "' + str(plugin) + '"\n'
                       'done\n')
        project = self.base / 'project with spaces'
        (project / '.venv/bin').mkdir(parents=True)
        (project / 'child').mkdir()
        python = project / '.venv/bin/python'
        python.write_text('#!/bin/sh\necho project-python\n')
        python.chmod(0o755)
        (project / '.envrc').write_text('export VIRTUAL_ENV="$PWD/.venv"\n'
                                      'PATH_add "$VIRTUAL_ENV/bin"\n')
        env = dict(self.env, VIRTUAL_ENV='previous-environment',
                   XDG_CONFIG_HOME=str(self.home / '.config'),
                   XDG_DATA_HOME=str(self.home / '.local/share'),
                   DIRENV_CONFIG=str(self.home / '.config/direnv'))
        for key in list(env):
            if key.startswith('DIRENV_') and key != 'DIRENV_CONFIG':
                env.pop(key)
        result = subprocess.run(
            ['/bin/zsh', '-f', '-c',
             'source "$1"; (( $+functions[_direnv_hook] )) || exit 1; '
             'original_path=$PATH; cd "$2"; '
             '[[ $VIRTUAL_ENV == previous-environment ]] || exit 2; '
             'direnv allow || exit 3; _direnv_hook; '
             '[[ $VIRTUAL_ENV == "$PWD/.venv" ]] || exit 4; '
             '[[ $(python) == project-python ]] || exit 5; '
             'cd child; [[ $(python) == project-python ]] || exit 6; '
             'cd "$3"; [[ $VIRTUAL_ENV == previous-environment ]] || exit 7; '
             '[[ $PATH == $original_path ]] || exit 8; '
             'print restored', 'probe', str(self.repo / 'stow/zsh/.zshrc'),
             str(project), str(self.home)],
            env=env, cwd=self.home, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('blocked', result.stderr)
        self.assertEqual(result.stdout.strip(), 'restored')

    def test_nvm_is_lazy_and_loads_on_first_node_command(self):
        plugin = Path(os.environ['HOME']) / '.oh-my-zsh/plugins/nvm/nvm.plugin.zsh'
        if not plugin.is_file():
            self.skipTest('Oh My Zsh nvm plugin is not installed')
        omz = self.home / '.oh-my-zsh/oh-my-zsh.sh'
        omz.parent.mkdir()
        omz.write_text('source "' + str(plugin) + '"\n')
        nvm = self.home / '.nvm/nvm.sh'
        nvm.parent.mkdir()
        nvm.write_text('print loaded >> "$HOME/nvm-loads"\n'
                       'node() { print fixture-node; }\n'
                       'nvm() { print fixture-nvm; }\n')
        env = dict(self.env)
        for key in list(env):
            if key.startswith('NVM_'):
                env.pop(key)
        result = subprocess.run(
            ['/bin/zsh', '-f', '-c',
             'source "$1"; [[ ! -e "$HOME/nvm-loads" ]] || exit 1; '
             'node; node; nvm', 'probe', str(self.repo / 'stow/zsh/.zshrc')],
            env=env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         ['fixture-node', 'fixture-node', 'fixture-nvm'])
        self.assertEqual((self.home / 'nvm-loads').read_text().splitlines(), ['loaded'])

    def test_zsh_preserves_initializers_without_local_override(self):
        self.stub('zoxide', 'printf "%s\\n" "$*" > "$HOME/zoxide-args"')
        for name, body in {
            '.oh-my-zsh/oh-my-zsh.sh': 'export OMZ_LOADED=yes\n'
                                     'path=("' + str(self.bin) + '" /usr/bin /bin)',
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
                                 'source "$1"; print -r -- "$OMZ_LOADED ${CONDA_LOADED:-absent} ${NVM_LOADED:-deferred} $TEST_API_KEY $HOMEBREW_NO_ANALYTICS"',
                                 'probe', str(self.repo / 'stow/zsh/.zshrc')],
                                env=env, cwd=self.repo, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'yes absent deferred  1')
        self.assertEqual(result.stderr, '')
        self.assertEqual((self.home / 'zoxide-args').read_text().strip(), 'init zsh')

    def test_shared_ssh_autostarts_tmux_only_without_remote_command(self):
        config = self.repo / 'stow/ssh/.ssh/config'
        local = self.home / '.ssh/config.local'
        local.parent.mkdir()
        local.write_text('Host fixture.invalid fixture-raw.invalid\n'
                         '  HostName server.invalid\n'
                         'Host fixture-raw.invalid\n'
                         '  RequestTTY yes\n'
                         '  RemoteCommand none\n')
        isolated = self.base / 'ssh_config'
        isolated.write_text(config.read_text().replace('Include ~/.ssh/config.local',
                                                      'Include ' + str(local)))
        cases = [
            (['fixture.invalid'], True, 'true'),
            (['fixture-raw.invalid'], False, 'true'),
            (['fixture.invalid', 'zsh'], False, 'auto'),
            (['fixture.invalid', 'true'], False, 'auto'),
            (['-s', 'fixture.invalid', 'sftp'], False, 'auto'),
        ]
        for args, autostart, tty in cases:
            with self.subTest(args=args):
                result = subprocess.run(['/usr/bin/ssh', '-G', '-F', str(isolated), *args],
                                        text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                values = dict(line.split(' ', 1) for line in result.stdout.splitlines())
                self.assertEqual(values.get('remotecommand', 'none'),
                                 '$SHELL -l -c "tmux new-session -A -s main"'
                                 if autostart else 'none')
                self.assertEqual(values['requesttty'], tty)
                self.assertEqual(values['hostname'], 'server.invalid')
                self.assertEqual(values['serveraliveinterval'], '30')
                self.assertEqual(values['serveralivecountmax'], '3')

    def test_ssh_tmux_uses_login_path_without_loading_interactive_config(self):
        self.stub('tmux', 'printf "%s\\n" "$*" > "$HOME/tmux-args"')
        (self.home / '.zprofile').write_text('export PATH="' + str(self.bin) + ':$PATH"\n')
        (self.home / '.zshrc').write_text('exit 91\n')
        config = self.repo / 'stow/ssh/.ssh/config'
        command = next(line.strip().removeprefix('RemoteCommand ')
                       for line in config.read_text().splitlines()
                       if line.strip().startswith('RemoteCommand '))
        result = subprocess.run(['/bin/zsh', '-f', '-c', command],
                                env=dict(self.env, SHELL='/bin/zsh'), cwd=self.repo,
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'tmux-args').read_text().strip(),
                         'new-session -A -s main')

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

    def test_shared_zsh_does_not_autostart_tmux(self):
        omz = self.home / '.oh-my-zsh/oh-my-zsh.sh'
        omz.parent.mkdir()
        omz.write_text('autoload -Uz compinit; compinit -u -d "$HOME/.zcompdump"\n')
        nvm = self.home / '.nvm/nvm.sh'
        nvm.parent.mkdir()
        nvm.write_text('export PATH="' + str(self.bin) + ':$PATH"\n')
        self.stub('tmux', 'printf "%s\\n" "$*" "$HOMEBREW_NO_ANALYTICS" >> "$HOME/tmux-args"')
        cases = [
            ('Apple_Terminal', '', '', True, True, False),
            ('iTerm.app', '', '', True, True, False),
            ('vscode', '', '', True, True, False),
            ('Apple_Terminal', 'fixture', '', True, True, False),
            ('Apple_Terminal', '', 'fixture', True, True, False),
            ('Apple_Terminal', '', '', False, True, False),
            ('Apple_Terminal', '', '', True, False, False),
        ]
        output = self.home / 'tmux-args'
        for terminal, tmux, ssh, interactive, tty, expected in cases:
            with self.subTest(terminal=terminal, tmux=tmux, ssh=ssh,
                              interactive=interactive, tty=tty):
                output.unlink(missing_ok=True)
                env = dict(self.env, TERM_PROGRAM=terminal, TMUX=tmux,
                           SSH_CONNECTION=ssh, TERM='xterm-256color')
                master, slave = pty.openpty()
                try:
                    result = subprocess.run(
                        ['/bin/zsh', '-f', *(['-i'] if interactive else []),
                         '-c', 'source "$1"', 'probe', str(self.repo / 'stow/zsh/.zshrc')],
                        stdin=slave if tty else subprocess.DEVNULL,
                        stdout=slave if tty else subprocess.PIPE, stderr=subprocess.PIPE,
                        env=env, cwd=self.repo, text=True, timeout=20)
                finally:
                    os.close(slave)
                    os.close(master)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output.exists(), expected)
                if expected:
                    self.assertEqual(output.read_text().splitlines(), ['new-session', '1'])

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
        self.assertEqual(tmux_run('show-options', '-sv', 'copy-command').stdout.strip(), '')
        self.assertEqual(tmux_run('show-options', '-sv', 'set-clipboard').stdout.strip(), 'external')
        self.assertEqual(tmux_run('show-options', '-gv', 'allow-passthrough').stdout.strip(), 'off')
        self.assertEqual(tmux_run('show-options', '-gv', 'default-terminal').stdout.strip(), 'tmux-256color')
        self.assertEqual(tmux_run('show-options', '-gv', 'default-command').stdout.strip(), '')

    def test_tmux_new_windows_and_splits_follow_directory_and_renumber(self):
        tmux = shutil.which('tmux', path=self.env['PATH'])
        if not tmux:
            self.skipTest('tmux is required')
        socket_dir = tempfile.TemporaryDirectory(prefix='df-layout-', dir='/tmp')
        self.addCleanup(socket_dir.cleanup)
        socket = str(Path(socket_dir.name) / 'socket')
        env = dict(self.env)
        env.pop('TMUX', None)

        def run(*args):
            result = subprocess.run([tmux, '-S', socket, *args], env=env,
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            return result.stdout.strip()

        self.addCleanup(lambda: subprocess.run([tmux, '-S', socket, 'kill-server'],
                                              env=env, capture_output=True))
        run('-f', str(self.repo / 'stow/tmux/.tmux.conf'), 'new-session', '-d',
            '-s', 'test', '-c', str(self.home), '/bin/zsh -f')
        run('set-option', '-g', 'default-command', '/bin/zsh -f')
        for option, expected in [('focus-events', 'on'), ('renumber-windows', 'on'),
                                 ('status-interval', '5'), ('visual-activity', 'off')]:
            self.assertEqual(run('show-options', '-gv', option), expected)
        self.assertEqual(run('show-options', '-gwv', 'monitor-activity'), 'on')
        run('send-keys', '-l', 'cd -- ' + shlex.quote(str(self.repo)))
        run('send-keys', 'Enter')
        deadline = time.monotonic() + 5
        while run('display-message', '-p', '#{pane_current_path}') != str(self.repo):
            self.assertLess(time.monotonic(), deadline, 'Shell did not change directory')
            time.sleep(0.05)
        for key, command in [('c', 'new-window'), ('v', 'split-window'),
                             ('s', 'split-window'), ('c', 'new-window')]:
            binding = shlex.split(next(line for line in run('list-keys', '-T', 'prefix').splitlines()
                                       if line.split()[3] == key))
            run(*binding[binding.index(command):])
            self.assertEqual(run('display-message', '-p', '#{pane_current_path}'), str(self.repo))
        self.assertEqual(run('list-panes', '-t', 'test:2', '-F', '#{pane_index}').splitlines(),
                         ['1', '2', '3'])
        run('kill-window', '-t', 'test:2')
        self.assertEqual(run('list-windows', '-F', '#{window_index}').splitlines(), ['1', '2'])

    def test_dependencies_are_explicit_and_fetch_latest_plugins_only_on_request(self):
        (self.home / '.zshrc').write_text('keep shell config')
        self.stub('brew', '''[ "$HOMEBREW_BUNDLE_NO_UPGRADE" = 1 ] || exit 92
for arg in "$@"; do
    case "$arg" in
        --file=*)
            for package in stow uv; do
                grep -qx "brew \\"$package\\"" "${arg#--file=}" || exit 93
            done ;;
    esac
done
printf "%s\\n" "$@" >> "$HOME/brew-args"''')
        self.stub('curl', 'printf "%s\\n" "$*" > "$HOME/curl-args"; while [ "$#" -gt 0 ]; do if [ "$1" = -o ]; then shift; : > "$1"; fi; shift; done')
        self.stub('git', 'printf "%s\\n" "$*" >> "$HOME/git-args"; mkdir -p "$4/tools" "$4/.git"; : > "$4/oh-my-zsh.sh"')
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
        plugin_root = self.home / '.oh-my-zsh/custom/plugins'
        for plugin in ('zsh-autosuggestions', 'zsh-syntax-highlighting'):
            self.assertTrue((plugin_root / plugin / '.git').is_dir())
            self.assertIn('https://github.com/zsh-users/' + plugin + '.git',
                          (self.home / 'git-args').read_text())
        (self.home / 'git-args').unlink()
        result = self.run_script('install.sh', 'deps')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / 'git-args').exists())

    def test_plugin_updates_respect_custom_directory(self):
        custom = self.home / 'custom plugins'
        self.env['ZSH_CUSTOM'] = str(custom)
        for plugin in ('zsh-autosuggestions', 'zsh-syntax-highlighting'):
            (custom / 'plugins' / plugin / '.git').mkdir(parents=True)
        self.stub('brew', 'exit 0')
        self.stub('git', 'printf "%s\\n" "$@" >> "$HOME/git-args"')
        result = self.run_script('install.sh', 'update')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / 'git-args').read_text().splitlines(), [
            '-C', str(custom / 'plugins/zsh-autosuggestions'), 'pull', '--ff-only',
            '-C', str(custom / 'plugins/zsh-syntax-highlighting'), 'pull', '--ff-only'])

    def git(self, *args):
        return subprocess.run(['/usr/bin/git', *args], cwd=self.repo, env=self.env,
                              check=True, text=True, capture_output=True)

    def test_version_and_unknown_option_do_not_install(self):
        self.assertEqual(self.run_script('install.sh', '--version').returncode, 0)
        self.assertNotEqual(self.run_script('install.sh', '--unknown').returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])



    def test_tailscale_alias_preserves_cli_without_gui(self):
        app = self.base / 'Tailscale.app/Contents/MacOS/Tailscale'
        config = self.repo / 'stow/zsh/.zshrc'
        config.write_text(config.read_text().replace(
            '/Applications/Tailscale.app/Contents/MacOS/Tailscale', str(app)))
        omz = self.home / '.oh-my-zsh/oh-my-zsh.sh'
        omz.parent.mkdir()
        omz.write_text('path=("' + str(self.bin) + '" /usr/bin /bin)\n')
        self.stub('zoxide', 'exit 0')
        self.stub('tailscale', 'echo fixture-cli')
        def invoke():
            return subprocess.run(['/bin/zsh', '-f', '-c',
                                   'source "$1"; eval tailscale', 'probe', str(config)],
                                  env=self.env, text=True, capture_output=True, timeout=10)
        result = invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'fixture-cli')
        app.parent.mkdir(parents=True)
        app.write_text('#!/bin/sh\necho fixture-gui\n')
        app.chmod(0o755)
        result = invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'fixture-gui')


if __name__ == '__main__':
    unittest.main()
