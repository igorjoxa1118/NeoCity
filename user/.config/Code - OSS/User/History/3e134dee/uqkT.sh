#!/bin/bash

input_name=$(ls ~/Загрузки/Video/Phone/thumbnals/ | grep '.mp4')

for name in ~/Загрузки/Video/Phone/thumbnals/"${input_name[@]}"; do
    output_name=$(echo $name | sed "s/.mp4/.jpg/g")
    #ffmpeg -update -i $name -ss 00:00:00 -vframes 1 ~/Загрузки/Video/Phone/thumbnals/test/$output_name
    echo "$output_name"
    echo "$name"
done

#echo "$output_name"