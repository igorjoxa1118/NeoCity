# Полностью пересоздаем конфиг
echo -e "Net/ThemeName \"catppuccin-mocha\"\nNet/IconThemeName \"TokyoNight-SE\"\nGtk/CursorThemeName \"catppuccin-mocha-mauve-cursors\"\nNet/EnableAnimations 0\nNet/EnableEventSounds 0\nNet/EnableInputFeedbackSounds 0" > ~/.xsettingsd

# Перезапускаем xsettingsd
pkill xsettingsd && xsettingsd &