import os
import pty
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FuzzySearch(unittest.TestCase):
    def setUp(self):
        if not all(shutil.which(tool, path='/opt/homebrew/bin:/usr/bin:/bin')
                   for tool in ('fzf', 'fd', 'rg')):
            self.skipTest('fzf, fd, and ripgrep are required')
        self.tmp = tempfile.TemporaryDirectory(prefix='df-fzf-')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = dict(os.environ, HOME=str(self.home), ZDOTDIR=str(self.home),
                        PATH='/opt/homebrew/bin:/usr/bin:/bin', TERM='xterm-256color',
                        GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                        FZF_DEFAULT_COMMAND='', FZF_DEFAULT_OPTS='')
        self.env.pop('TMUX', None)
        subprocess.run(['/usr/bin/git', '-c', 'init.templateDir=', 'init', '-q'],
                       cwd=self.home, env=self.env, check=True)
        (self.home / '.gitignore').write_text('ignored.txt\n')
        (self.home / 'ignored.txt').write_text('needle ignored\n')
        (self.home / '.hidden.txt').write_text('needle hidden\n')
        (self.home / 'file with spaces.txt').write_text('first\nneedle here\n')

    def test_zsh_widgets_and_fd_candidates(self):
        plugin = Path(os.environ['HOME']) / '.oh-my-zsh/plugins/fzf/fzf.plugin.zsh'
        if not plugin.is_file():
            self.skipTest('Oh My Zsh fzf plugin is not installed')
        omz = self.home / '.oh-my-zsh/oh-my-zsh.sh'
        omz.parent.mkdir()
        omz.write_text('autoload -Uz compinit\ncompinit -D\nbindkey -v\n'
                       'for plugin in $plugins; do\n'
                       '  [[ $plugin == fzf ]] && source "' + str(plugin) + '"\n'
                       'done\n')
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        result = subprocess.run(
            ['/bin/zsh', '-f', '-i', '-c',
             'source "$1"; print -r -- "$EDITOR"; '
             'bindkey -M viins "^T"; bindkey -M viins "^R"; bindkey -M viins "\\ec"; '
             'eval "$FZF_DEFAULT_COMMAND"', 'probe', str(ROOT / 'stow/zsh/.zshrc')],
            cwd=self.home, env=self.env, stdin=slave, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], 'vim')
        self.assertIn('fzf-file-widget', lines[1])
        self.assertIn('fzf-history-widget', lines[2])
        self.assertIn('fzf-cd-widget', lines[3])
        self.assertIn('file with spaces.txt', lines[4:])
        self.assertIn('.hidden.txt', lines[4:])
        self.assertNotIn('ignored.txt', lines[4:])
        self.assertFalse(any(line.startswith('.git/') for line in lines[4:]))

    def test_vim_file_search_content_location_and_buffer_switch(self):
        plugin = Path(os.environ['HOME']) / '.vim/plugged/fzf.vim'
        if not (plugin / 'plugin/fzf.vim').is_file():
            self.skipTest('fzf.vim is not installed')
        output = self.home / 'result'
        script = self.home / 'probe.vim'
        # --print-query supplies the leading dispatch line normally produced by
        # interactive --expect; --filter selects deterministically without a UI.
        script.write_text(
            'set runtimepath+=/opt/homebrew/opt/fzf\n'
            'execute "set runtimepath+=" . fnameescape("' + str(plugin) + '")\n'
            'runtime! plugin/fzf.vim\n'
            'let g:fzf_vim = {"preview_window": []}\n'
            'let $FZF_DEFAULT_OPTS = "--filter=spaces --print-query"\n'
            'call feedkeys("\\<C-p>", "xt")\nsleep 1\n'
            'let file = expand("%:t")\n'
            'let $FZF_DEFAULT_OPTS = "--filter=spaces --print-query"\n'
            'Rg needle\nsleep 1\nlet position = line(".")\n'
            'edit other.txt\n'
            'let $FZF_DEFAULT_OPTS = "--filter=spaces --print-query"\n'
            'call feedkeys(",b", "xt")\nsleep 1\n'
            'call writefile([file, string(position), expand("%:t")], "' + str(output) + '")\nqa!\n')
        result = subprocess.run(
            ['/usr/bin/vim', '-N', '-u', str(ROOT / 'stow/vim/.vimrc'),
             '-i', 'NONE', '-n', '-es', '-V1', '-S', str(script)],
            cwd=self.home, env=self.env, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text().splitlines(),
                         ['file with spaces.txt', '2', 'file with spaces.txt'])
