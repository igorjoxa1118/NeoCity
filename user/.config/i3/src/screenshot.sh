#!/usr/bin/env sh

# Директория для сохранения
SAVE_DIR="$HOME/Изображения"
mkdir -p "$SAVE_DIR"

# Уникальное имя файла
FILENAME="screenshot_$(date +'%Y-%m-%d_%H-%M-%S').png"
FULL_PATH="$SAVE_DIR/$FILENAME"

# Делаем скриншот:
# -s : выбор области (select)
# -u : скрыть курсор со снимка
# --noopengl : отключает использование OpenGL для выделения (убирает эффекты)
maim -s -u --noopengl "$FULL_PATH"

# Проверяем результат
if [ -f "$FULL_PATH" ]; then
    # Копируем в буфер обмена
    xclip -selection clipboard -t image/png -i "$FULL_PATH"
    
    # Уведомление
    notify-send "Скриншот сделан" "Файл: $FILENAME" -i "$FULL_PATH"
else
    notify-send "Скриншот отменен"
fi