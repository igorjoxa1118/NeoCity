if functions -q deactivate-lua
    deactivate-lua
end

function deactivate-lua
    if test -x '/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin/lua'
        eval ('/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin/lua' '/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin/get_deactivated_path.lua' --fish)
    end

    functions -e deactivate-lua
end

set -gx PATH '/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin' $PATH
