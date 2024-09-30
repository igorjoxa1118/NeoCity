-- LuaRocks configuration

rocks_trees = {
   { name = "user", root = home .. "/.luarocks" };
   { name = "system", root = "/home/vir0id/.local/share/nvim/lazy-rocks/hererocks" };
}
variables = {
   LUA_DIR = "/home/vir0id/.local/share/nvim/lazy-rocks/hererocks";
   LUA_BINDIR = "/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin";
   LUA_VERSION = "5.1";
   LUA = "/home/vir0id/.local/share/nvim/lazy-rocks/hererocks/bin/lua";
}
