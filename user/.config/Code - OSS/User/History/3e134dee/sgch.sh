#!/bin/bash

input_name=$(ls ~/Загрузки/Video/Phone/thumbnals/ | grep '.mp4' | sed 's/.\{4\}$//')
output_name=$(ls ~/Загрузки/Video/Phone/thumbnals/test | sed 's/.\{4\}$//')

for name in "${input_name[@]}"; do
    ffmpeg -i $name.mp4 -ss 00:00:00 -vframes 1 ~/Загрузки/Video/Phone/thumbnals/test/$name.png
    echo "$name.mp4"
done

#echo "$output_name"