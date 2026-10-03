import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VimConfiguration(unittest.TestCase):
    def probe(self, commands):
        with tempfile.TemporaryDirectory(prefix='df-vim-') as directory:
            home = Path(directory)
            result_file = home / 'result'
            script = home / 'probe.vim'
            script.write_text(commands.replace('RESULT', str(result_file)).replace('CONFIG', str(ROOT / 'stow/vim/.vimrc')) + '\nqa!\n')
            result = subprocess.run(
                ['/usr/bin/vim', '-N', '-u', str(ROOT / 'stow/vim/.vimrc'),
                 '-i', 'NONE', '-n', '-es', '-V1', '-S', str(script)],
                env=dict(os.environ, HOME=directory, ZDOTDIR=directory, LANG='en_US.UTF-8'),
                cwd=directory, text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result_file.read_text().splitlines()

    def test_reload_does_not_duplicate_autocommands(self):
        self.assertEqual(self.probe(r'''
let before = execute('autocmd FocusGained')
execute 'source ' . fnameescape('CONFIG')
let after = execute('autocmd FocusGained')
call writefile([string(len(filter(split(before, "\n"), 'v:val =~# "checktime$"'))), string(len(filter(split(after, "\n"), 'v:val =~# "checktime$"')))], 'RESULT')
'''), ['1', '1'])

    def test_buffer_close_preserves_shared_splits(self):
        self.assertEqual(self.probe(r'''
let original = bufnr('%')
vsplit
let windows = map(getwininfo(), 'v:val.winid')
call feedkeys(',bd', 'xt')
call writefile([string(map(getwininfo(), 'v:val.winid') == windows), string(buflisted(original))], 'RESULT')
'''), ['1', '0'])

    def test_last_tab_survives_tab_renumbering_and_deletion(self):
        self.assertEqual(self.probe(r'''
tabnew
tabnew
let target = win_getid()
tabfirst
tabclose 2
call feedkeys(',tl', 'xt')
let reached = win_getid() == target
tabfirst
tabclose 2
call feedkeys(',tl', 'xt')
call writefile([string(reached), string(tabpagenr('$'))], 'RESULT')
'''), ['1', '1'])

    def test_visual_search_preserves_yank_registers(self):
        self.assertEqual(self.probe(r'''
call setline(1, ['first selection', 'second'])
call setreg('0', ['previous', 'yank'], 'V')
normal! "ayy
let zero = getreginfo('0')
let unnamed = getreginfo('"')
call feedkeys('vll*', 'xt')
call writefile([string(getreginfo('0') == zero), string(getreginfo('"') == unnamed), string(@/ != '')], 'RESULT')
'''), ['1', '1', '1'])

    def test_locale_and_indentation_follow_the_environment_and_shiftwidth(self):
        self.assertEqual(self.probe(r'''
call feedkeys("ia\<Tab>x\<Esc>", 'xt')
let four = getline(1)
enew!
setlocal shiftwidth=2
call feedkeys("ia\<Tab>x\<Esc>", 'xt')
call writefile([$LANG, four, getline(1)], 'RESULT')
'''), ['en_US.UTF-8', 'a   x', 'a x'])

    def test_removed_templates_do_not_insert_file_contents(self):
        self.assertEqual(self.probe(r'''
let g:dotfiles_enable_file_templates = 1
edit fresh.py
call writefile([string(line('$')), getline(1), string(&undofile)], 'RESULT')
'''), ['1', '', '0'])

    def test_ale_does_not_enable_unconfigured_linters(self):
        plugin = Path.home() / '.vim/plugged/ale'
        if not (plugin / 'autoload/ale/linter.vim').is_file():
            self.skipTest('ALE is not installed in the test host')
        self.assertEqual(self.probe(
            'execute "set runtimepath^=" . fnameescape("' + str(plugin) + '")\nruntime plugin/ale.vim\n' + r'''
call ale#linter#Define('unconfigured', {'name': 'probe', 'executable': 'true', 'command': 'true', 'callback': 'UnusedProbe'})
let explicit = ale#linter#Get('unconfigured')
let g:ale_linters_explicit = 0
let default = ale#linter#Get('unconfigured')
call writefile([string(empty(explicit)), string(len(default))], 'RESULT')
'''), ['1', '1'])

    def test_new_shell_script_remains_empty(self):
        self.assertEqual(self.probe(r'''
execute 'source ' . fnameescape('CONFIG')
edit fresh.sh
call writefile([string(line('$')), getline(1)], 'RESULT')
'''), ['1', ''])

    def test_existing_shell_scripts_are_unchanged(self):
        self.assertEqual(self.probe(r'''
call writefile([], 'empty.sh')
call writefile(['#!/bin/sh', 'echo existing'], 'existing.sh')
edit empty.sh
let empty_file = getline(1)
edit existing.sh
call writefile([empty_file] + getline(1, '$'), 'RESULT')
'''), ['', '#!/bin/sh', 'echo existing'])
