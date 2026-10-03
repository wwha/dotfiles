"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Fork from  https://github.com/amix/vimrc
"
" Sections:
"    -> General
"    -> VIM user interface
"    -> Colors and Fonts
"    -> Files and backups
"    -> Text, tab and indent related
"    -> Visual mode related
"    -> Moving around, tabs and buffers
"    -> Status line
"    -> Editing mappings
"    -> vimgrep searching and cope displaying
"    -> Spell checking
"    -> Misc
"    -> Helper functions
"
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => General
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Sets how many lines of history VIM has to remember
set history=500

" Set encoding before defining Unicode display characters.
set encoding=utf8

" Enable filetype plugins
filetype plugin on
filetype indent on

" Set to auto read when a file is changed from the outside
set autoread
augroup dotfiles_autoread
    autocmd!
    autocmd FocusGained,BufEnter * checktime
augroup END

" With a map leader it's possible to do extra key combinations
" like <leader>w saves the current file
let mapleader = ","

" Fast saving
nnoremap <leader>w :w<cr>



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => VIM user interface
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Set 7 lines to the cursor - when moving vertically using j/k
set so=7

" Turn on the Wild menu
set wildmenu

" Ignore compiled files
set wildignore=*.o,*~,*.pyc
set wildignore+=*/.git/*,*/.hg/*,*/.svn/*,*/.DS_Store

" Always show current position
set ruler

" Height of the command bar
set cmdheight=1

" A buffer becomes hidden when it is abandoned
set hid

" Configure backspace so it acts as it should act
set backspace=eol,start,indent
set whichwrap+=<,>,h,l

" Ignore case when searching
set ignorecase

" When searching try to be smart about cases
set smartcase

" Highlight search results
set hlsearch

" Makes search act like search in modern browsers
set incsearch

" Don't redraw while executing macros (good performance config)
set lazyredraw

" For regular expressions turn magic on
set magic

" Show matching brackets when text indicator is over them
set showmatch

" How many tenths of a second to blink when matching brackets
set mat=2

" No annoying sound on errors
set noerrorbells
set novisualbell
set t_vb=
set tm=500

" Add a bit extra margin to the left
set foldcolumn=1

" Show line numbers
set number

" Show/hide tabstops and EOLs
" nnoremap <leader>l :set list!<CR> conflicts with other shortcuts

" Use the same symbols as TextMate for tabstops and EOLs
set listchars=tab:▸\ ,eol:¬


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Colors and Fonts
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Enable syntax highlighting
syntax enable

" iTerm2 supports true color; tmux advertises RGB for its xterm client.
set termguicolors

try
    colorscheme desert
catch
endtry

set background=dark

" Use Unix as the standard file type
set ffs=unix,dos,mac


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Files, backups and undo
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Keep Vim's recovery and backup defaults.


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Text, tab and indent related
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Use spaces instead of tabs
set expandtab

" Be smart when using tabs ;)
set smarttab

" 1 tab == 4 spaces
set shiftwidth=4
set tabstop=4
set softtabstop=-1

" Wrap for display without inserting hard line breaks
set lbr
set textwidth=0

set ai "Auto indent
set wrap "Wrap lines


""""""""""""""""""""""""""""""
" => Visual mode related
""""""""""""""""""""""""""""""
" Visual mode pressing * or # searches for the current selection
" Super useful! From an idea by Michael Naumann
vnoremap <silent> * :<C-u>call VisualSelection()<CR>/<C-R>=@/<CR><CR>
vnoremap <silent> # :<C-u>call VisualSelection()<CR>?<C-R>=@/<CR><CR>


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Moving around, tabs, windows and buffers
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Map <Space> to / (search) and Ctrl-<Space> to ? (backwards search)
nnoremap <space> /
nnoremap <C-space> ?

" Disable highlight when <leader><cr> is pressed
nnoremap <silent> <leader><cr> :noh<cr>

" vim-tmux-navigator handles Ctrl-h/j/k/l across Vim and tmux panes.
let g:tmux_navigator_disable_when_zoomed = 1

" Close the current buffer
nnoremap <leader>bd :Bclose<cr>

" Close all the buffers
nnoremap <leader>ba :bufdo bd<cr>

nnoremap <leader>l :bnext<cr>
nnoremap <leader>h :bprevious<cr>

" Useful mappings for managing tabs
nnoremap <leader>tn :tabnew<cr>
nnoremap <leader>to :tabonly<cr>
nnoremap <leader>tc :tabclose<cr>
nnoremap <leader>tm :tabmove
nnoremap <leader>t<leader> :tabnext

" Let 'tl' toggle between this and the last accessed tab
let g:dotfiles_lasttab_winid = get(g:, 'dotfiles_lasttab_winid', 0)
nnoremap <Leader>tl :call <SID>LastTab()<CR>
augroup dotfiles_tabs
    autocmd!
    autocmd TabLeave * let g:dotfiles_lasttab_winid = win_getid()
augroup END

function! s:LastTab()
    let target = win_id2tabwin(g:dotfiles_lasttab_winid)[0]
    if target > 0
        execute 'tabnext ' . target
    endif
endfunction


" Opens a new tab with the current buffer's path
" Super useful when editing files in the same directory
nnoremap <leader>te :tabedit <C-r>=expand("%:p:h")<cr>/

" Switch CWD to the directory of the open buffer
nnoremap <leader>cd :cd %:p:h<cr>:pwd<cr>

" Specify the behavior when switching between buffers
try
  set switchbuf=useopen,usetab,newtab
  set stal=2
catch
endtry

" Return to last edit position when opening files (You want this!)
augroup dotfiles_last_position
    autocmd!
    autocmd BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
augroup END


""""""""""""""""""""""""""""""
" => Status line
""""""""""""""""""""""""""""""
" Always show the status line
set laststatus=2

" Format the status line
set statusline=\ %{HasPaste()}%F%m%r%h\ %w\ \ CWD:\ %r%{getcwd()}%h\ \ \ Line:\ %l\ \ Column:\ %c


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Editing mappings
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Remap VIM 0 to first non-blank character
nnoremap 0 ^

" Move a line of text using ALT+[jk] or Command+[jk] on mac
nnoremap <leader>j mz:m+<cr>`z
nnoremap <leader>k mz:m-2<cr>`z
xnoremap <M-j> :m'>+<cr>`<my`>mzgv`yo`z
xnoremap <M-k> :m'<-2<cr>`>my`<mzgv`yo`z

" Map <j,k> to esc
inoremap jk <Esc>

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Remote Clipboard (OSC 52)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" This allows yanking from Vim over SSH/Tmux to the local clipboard.
" Requires a terminal that supports OSC 52 (e.g., iTerm2, Kitty, Alacritty).
function! Osc52Yank()
    if $TMUX != ''
        call system('tmux load-buffer -w -', getreg('0'))
        if v:shell_error
            echoerr 'OSC 52: tmux clipboard copy failed'
        endif
        return
    endif
    let b64 = substitute(system('base64', getreg('0')), '\n', '', 'g')
    if v:shell_error
        echoerr 'OSC 52: base64 failed'
        return
    endif
    let sequence = "\e]52;c;" . b64 . "\x07"
    call writefile([sequence], "/dev/tty", "b")
endfunction

" Explicit clipboard copy; ordinary yanks keep their Vim register behavior.
nnoremap <silent> <leader>y yy:call Osc52Yank()<CR>
xnoremap <silent> <leader>y y:call Osc52Yank()<CR>


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Spell checking
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Pressing ,ss will toggle and untoggle spell checking
nnoremap <leader>ss :setlocal spell!<cr>

" Shortcuts using <leader>
nnoremap <leader>sn ]s
nnoremap <leader>sp [s
nnoremap <leader>sa zg
nnoremap <leader>s? z=


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Misc
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Remove the Windows ^M - when the encodings gets messed up
noremap <Leader>m mmHmt:%s/<C-V><cr>//ge<cr>'tzt'm

" Quickly open a buffer for scribble
nnoremap <leader>q :e ~/buffer<cr>

" Quickly open a markdown buffer for scribble
nnoremap <leader>x :e ~/buffer.md<cr>

" Toggle paste mode on and off
nnoremap <leader>pp :setlocal paste!<cr>


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Helper functions
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Returns true if paste mode is enabled
function! HasPaste()
    if &paste
        return 'PASTE MODE  '
    endif
    return ''
endfunction

" Don't close window, when deleting a buffer
command! Bclose call <SID>BufcloseCloseIt()
function! <SID>BufcloseCloseIt()
    let current = bufnr('%')
    if getbufvar(current, '&modified')
        echoerr 'No write since last change; save the buffer before closing it'
        return
    endif
    let replacement = bufnr('#')
    if replacement == current || !buflisted(replacement)
        let candidates = filter(getbufinfo({'buflisted': 1}), 'v:val.bufnr != current')
        let replacement = empty(candidates) ? bufadd('') : candidates[0].bufnr
    endif
    call setbufvar(replacement, '&buflisted', 1)
    for window in getwininfo()
        if window.bufnr == current
            call win_execute(window.winid, 'buffer ' . replacement)
        endif
    endfor
    execute 'bdelete ' . current
endfunction

function! VisualSelection() range
    let saved_unnamed = getreginfo('"')
    let saved_zero = getreginfo('0')
    try
        execute "normal! vgvy"
        let pattern = escape(@", "\\/.*'$^~[]")
        let @/ = substitute(pattern, '\n$', '', '')
    finally
        call setreg('"', saved_unnamed)
        call setreg('0', saved_zero)
    endtry
endfunction

" Vim-plug configuration
" Run :PlugInstall in Vim to install plugins
if !empty(glob('~/.vim/autoload/plug.vim'))
call plug#begin('~/.vim/plugged')

" Essential plugins
Plug '/opt/homebrew/opt/fzf'           " Homebrew fzf Vim runtime
Plug 'junegunn/fzf.vim'                " File and content finder
Plug 'scrooloose/nerdtree'             " File explorer
Plug 'dense-analysis/ale'              " Linter
Plug 'christoomey/vim-tmux-navigator'   " Vim/tmux pane navigation

call plug#end()
endif

" fzf.vim; the fallback also covers Vim launched without interactive Zsh.
if empty($FZF_DEFAULT_COMMAND)
    let $FZF_DEFAULT_COMMAND = 'fd --type f --hidden --exclude .git'
endif
nnoremap <silent> <C-p> :Files<CR>
nnoremap <leader>rg :Rg<Space>
nnoremap <silent> <leader>b :Buffers<CR>

" ALE Configuration
let g:ale_linters_explicit = 1
let g:ale_linters = {
\   'python': ['ruff'],
\   'javascript': ['eslint'],
\   'c': ['clangd'],
\   'cpp': ['clangd'],
\   'markdown': ['markdownlint'],
\   'sh': [],
\   'zsh': [],
\}

" Keep linting disabled for local environment files
let g:ale_pattern_options = {
\   '\.env.*$': {'ale_enabled': 0},
\}

" Run configured fixers on save.
let g:ale_fix_on_save = 1

let g:ale_fixers = {
\   'python': ['ruff', 'ruff_format'],
\   'c': ['clang-format'],
\   'cpp': ['clang-format'],
\   'markdown': ['prettier'],
\}

" Linter specific options
let g:ale_markdown_markdownlint_options = '--disable MD013'

" Use a consistent sign for errors and warnings
let g:ale_sign_error = '>>'
let g:ale_sign_warning = '--'

" Navigation shortcuts
nmap <silent> <leader>an <Plug>(ale_next_wrap)
nmap <silent> <leader>ap <Plug>(ale_previous_wrap)
nnoremap <silent> <leader>af :ALEFix<cr>

" NERDTree Configuration
nnoremap <C-n> :NERDTreeToggle<CR>
let NERDTreeShowHidden=1
let NERDTreeIgnore = ['\.pyc$', '\.o$', '\.obj$']
