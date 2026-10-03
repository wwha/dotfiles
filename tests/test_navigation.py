import os
import fcntl
import base64
from pathlib import Path
import pty
import re
import select
import shlex
import sys
import shutil
import subprocess
import struct
import tempfile
import time
import termios
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Navigation(unittest.TestCase):
    def test_vim_tmux_navigation_and_zoom(self):
        plugin = Path(os.environ.get('DOTFILES_NAVIGATOR_PATH',
                                     str(Path.home() / '.vim/plugged/vim-tmux-navigator')))
        if not (plugin / 'plugin/tmux_navigator.vim').is_file():
            self.skipTest('vim-tmux-navigator is not installed')
        tmux = shutil.which('tmux')
        vim = shutil.which('vim')
        if not tmux or not vim:
            self.skipTest('Vim and tmux are required')
        with tempfile.TemporaryDirectory(prefix='df-nav-', dir='/tmp') as directory:
            base = Path(directory)
            home = base / 'home'
            home.mkdir()
            env = dict(os.environ, HOME=str(home), ZDOTDIR=str(home),
                       TERM='xterm-256color', SHELL='/bin/zsh')
            env.pop('TMUX', None)
            socket = str(base / 'socket')

            def run(*args):
                result = subprocess.run([tmux, '-S', socket, *args], env=env,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout.strip()

            def wait_for(predicate):
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if predicate():
                        return
                    time.sleep(0.05)
                self.fail('Navigation did not reach the expected state; '
                          'Vim=' + vim + '; state=' + (state.read_text() if state.exists() else 'missing') +
                          '; pane=' + run('display-message', '-p', '#{pane_id}') +
                          '; screen=' + run('capture-pane', '-p', '-t', vim_pane))

            state = base / 'state'
            script = base / 'start.vim'
            script.write_text(
                'set runtimepath+=' + str(plugin) + '\n'
                'runtime plugin/tmux_navigator.vim\n'
                'vsplit\nwincmd h\n'
                'let g:state_file = "' + str(state) + '"\n'
                'function! ReportWindow()\n'
                '  call writefile([string(winnr()), maparg("<C-l>", "n"), mode()], g:state_file . ".tmp")\n'
                '  call rename(g:state_file . ".tmp", g:state_file)\n'
                'endfunction\n'
                'nnoremap <silent> <F6> :call ReportWindow()<CR>\n'
                'call writefile(["ready"], "' + str(state) + '")\n')
            master, slave = pty.openpty()
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 160, 0, 0))
            output = bytearray()
            stop_reader = threading.Event()

            def drain():
                try:
                    while not stop_reader.is_set():
                        if not select.select([master], [], [], 0.1)[0]:
                            continue
                        chunk = os.read(master, 65536)
                        if not chunk:
                            return
                        output.extend(chunk)
                except OSError:
                    pass

            reader = threading.Thread(target=drain, daemon=True)
            reader.start()
            client = None
            try:
                # Only this temporary socket is touched; no real HOME config is loaded.
                run('-f', str(ROOT / 'stow/tmux/.tmux.conf'), 'new-session', '-d',
                    '-s', 'test', vim, '-N', '-u', str(ROOT / 'stow/vim/.vimrc'),
                    '-i', 'NONE', '-S', str(script))
                vim_pane = run('display-message', '-p', '#{pane_id}')
                shell_pane = run('split-window', '-h', '-P', '-F', '#{pane_id}', '/bin/zsh', '-f')
                run('select-pane', '-t', vim_pane)
                client = subprocess.Popen([tmux, '-S', socket, 'attach-session', '-t', 'test'],
                                          env=env, stdin=slave, stdout=slave, stderr=slave)
                wait_for(lambda: state.exists() and state.read_text().strip() == 'ready')
                wait_for(lambda: bool(run('list-clients')))

                def active():
                    return run('display-message', '-p', '#{pane_id}')

                def window_number():
                    state.unlink(missing_ok=True)
                    run('send-keys', '-t', vim_pane, 'F6')
                    wait_for(state.exists)
                    return state.read_text().partition('\n')[0]

                # The startup script can finish before the attached client is
                # ready for input. Confirm Vim processes a key before navigating.
                wait_for(lambda: window_number() == '1')
                os.write(master, b'\x0c')  # Ctrl-l: move within Vim first.
                wait_for(lambda: window_number() == '2')
                self.assertEqual(active(), vim_pane)
                os.write(master, b'\x0c')  # The outer Vim edge crosses into tmux.
                wait_for(lambda: active() == shell_pane)
                os.write(master, b'\x08')  # Ctrl-h: shell back to Vim.
                wait_for(lambda: active() == vim_pane)
                run('resize-pane', '-t', vim_pane, '-Z')
                os.write(master, b'\x0c')
                time.sleep(0.2)
                self.assertEqual(active(), vim_pane)
                self.assertEqual(run('display-message', '-p', '#{window_zoomed_flag}'), '1')

                # Verify emitted OSC 52 bytes, without touching a system clipboard.
                run('send-keys', '-t', vim_pane, ':call setline(1, "Vim clipboard probe")', 'Enter')
                offset = len(output)
                run('send-keys', '-t', vim_pane, ',y')
                def clipboard_payloads():
                    matches = re.findall(rb'\x1b\]52;[^;]*;([A-Za-z0-9+/=]+)(?:\x07|\x1b\\)',
                                         bytes(output[offset:]))
                    return [base64.b64decode(value) for value in matches]

                wait_for(lambda: b'Vim clipboard probe\n' in clipboard_payloads())

                run('resize-pane', '-t', vim_pane, '-Z')
                run('select-pane', '-t', shell_pane)
                run('send-keys', '-t', shell_pane,
                    "printf 'tmux clipboard probe\\n'; sleep 60", 'Enter')
                wait_for(lambda: 'tmux clipboard probe' in run('capture-pane', '-p', '-t', shell_pane))
                offset = len(output)
                run('copy-mode', '-t', shell_pane)
                run('send-keys', '-t', shell_pane, '-X', 'search-backward', 'tmux clipboard probe')
                run('send-keys', '-t', shell_pane, '-X', 'start-of-line')
                run('send-keys', '-t', shell_pane, '-X', 'begin-selection')
                run('send-keys', '-t', shell_pane, '-X', 'end-of-line')
                run('send-keys', '-t', shell_pane, '-X', 'copy-selection-and-cancel')

                def copied_by_tmux():
                    return any(b'tmux clipboard probe' in value for value in clipboard_payloads())

                wait_for(copied_by_tmux)

                # Unrequested output must neither reach the client clipboard nor
                # replace tmux's buffer. Emit via a file so shell echo cannot
                # contain the escape sequences we are trying to detect.
                payload = b'unrequested clipboard probe'
                raw = b'\x1b]52;c;' + base64.b64encode(payload) + b'\x07'
                wrapped = b'\x1bPtmux;' + raw.replace(b'\x1b', b'\x1b\x1b') + b'\x1b\\'
                emitter = base / 'emit.py'
                emitter.write_text('import sys\n'
                                   'sys.stdout.buffer.write(' + repr(raw + wrapped) + ')\n'
                                   'print("blocked-output-complete", flush=True)\n')
                previous_buffer = run('show-buffer')
                offset = len(output)
                run('send-keys', '-t', shell_pane, 'C-c')
                run('send-keys', '-t', shell_pane,
                    shlex.quote(sys.executable) + ' ' + shlex.quote(str(emitter)), 'Enter')
                wait_for(lambda: 'blocked-output-complete' in run('capture-pane', '-p', '-t', shell_pane))
                time.sleep(0.2)  # Allow the PTY reader to consume the final output.
                self.assertNotIn(payload, clipboard_payloads())
                self.assertEqual(run('show-buffer'), previous_buffer)
            finally:
                subprocess.run([tmux, '-S', socket, 'kill-server'], env=env,
                               capture_output=True, timeout=10)
                if client is not None:
                    client.wait(timeout=5)
                stop_reader.set()
                reader.join(timeout=1)
                os.close(slave)
                os.close(master)
