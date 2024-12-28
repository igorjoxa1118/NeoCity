-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")

vim.api.nvim_create_autocmd("VimEnter", {
    command = "set nornu nonu | Neotree toggle",
  })
  vim.api.nvim_create_autocmd("BufEnter", {
    command = "set rnu nu",
  })