#!/bin/bash

input_name=$(ls ~/Загрузки/Video/Phone/thumbnals/ | grep '.mp4')
output_name=$(ls ~/Загрузки/Video/Phone/thumbnals/ | grep '.mp4' | sed "s/.mp4/.jpg/g")


ffmpeg -update -i $input_name -ss 00:00:00 -vframes 1 ~/Загрузки/Video/Phone/thumbnals/test/$output_name



