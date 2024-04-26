#!/bin/bash

input_name=$(ls ~/Загрузки/Video/Phone/thumbnals/ | grep '.mp4' | sed 's/.\{4\}$//')
output_name=$(ls ~/Загрузки/Video/Phone/thumbnals/test | sed 's/.\{4\}$//')

for name in ~/Загрузки/Video/Phone/thumbnals/; do
    ffmpeg -i $input_name -ss 00:00:00 -vframes 1 ~/Загрузки/Video/Phone/thumbnals/test/$output_name.png
    #echo "$thumb_name"
done

#echo "$output_name"