return {
  "nvim-telescope/telescope.nvim",
  dependencies = {
    "nvim-telescope/telescope-fzf-native.nvim",
    build = "make",
    config = function()
      require("telescope").load_extension("fzf")
    end,
  },
  keys = {
    -- Основные команды поиска
    { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find Files" },
    { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live Grep" },
    { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Buffers" },
    { "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "Help Tags" },
    -- Git команды
    { "<leader>gf", "<cmd>Telescope git_files<cr>", desc = "Git Files" },
    { "<leader>gc", "<cmd>Telescope git_commits<cr>", desc = "Git Commits" },
    { "<leader>gs", "<cmd>Telescope git_status<cr>", desc = "Git Status" },
  },
  opts = {
    defaults = {
      -- Внешний вид
      prompt_prefix = "🔍 ",
      selection_caret = "❯ ",
      path_display = { "truncate" },
      selection_strategy = "reset",
      sorting_strategy = "ascending",
      layout_strategy = "horizontal",

      -- Настройки макета
      layout_config = {
        horizontal = {
          prompt_position = "top",
          preview_width = 0.55,
          results_width = 0.8,
        },
        vertical = {
          mirror = false,
        },
        width = 0.87,
        height = 0.80,
        preview_cutoff = 120,
      },

      -- Игнорируемые файлы и папки
      file_ignore_patterns = {
        "node_modules",
        "build",
        "dist",
        "yarn.lock",
        ".git",
        ".next",
      },

      -- Настройки поиска
      vimgrep_arguments = {
        "rg",
        "--color=never",
        "--no-heading",
        "--with-filename",
        "--line-number",
        "--column",
        "--smart-case",
      },

      -- Маппинги в окне Telescope
      mappings = {
        i = {
          ["<C-j>"] = "move_selection_next",
          ["<C-k>"] = "move_selection_previous",
          ["<C-q>"] = "close",
          ["<C-u>"] = "preview_scrolling_up",
          ["<C-d>"] = "preview_scrolling_down",
        },
      },
    },

    -- Настройки расширений
    extensions = {
      fzf = {
        fuzzy = true,
        override_generic_sorter = true,
        override_file_sorter = true,
        case_mode = "smart_case",
      },
    },

    -- Настройки для поиска файлов
    pickers = {
      find_files = {
        hidden = true,
        no_ignore = false,
        follow = true,
      },
      live_grep = {
        additional_args = function()
          return { "--hidden" }
        end,
      },
      buffers = {
        show_all_buffers = true,
        sort_lastused = true,
        previewer = false,
        mappings = {
          i = {
            ["<c-d>"] = "delete_buffer",
          },
        },
      },
    },
  },
}
