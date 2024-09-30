#!/bin/bash

input_name=$(ls ~/Загрузки/Video/Phone/thumbnals/ | grep '.mp4')
output_name=$(ls ~/Загрузки/Video/Phone/thumbnals/ | grep '.mp4' | sed "s/.mp4/.jpg/g")

for name in "${input_name[@]}"; do
    ffmpeg -i $name -ss 00:00:00 -vframes 1 ~/Загрузки/Video/Phone/thumbnals/test/$output_name
    #echo $name
done

#echo "$output_name"