which deactivate-lua >&/dev/null && deactivate-lua

alias deactivate-lua 'if ( -x '\''/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin/lua'\'' ) then; setenv PATH `'\''/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin/lua'\'' '\''/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin/get_deactivated_path.lua'\''`; rehash; endif; unalias deactivate-lua'

setenv PATH '/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin':"$PATH"
rehash
