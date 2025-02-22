#!/bin/bash

bar="▁▂▃▄▅▆▇█"
dict="s/;//g"

bar_length=${#bar}

for ((i = 0; i < bar_length; i++)); do
	dict+=";s/$i/${bar:$i:1}/g"
done

config_file="/tmp/bar_cava_config"
cat >"$config_file" <<EOF
[general]
bars = 15

[input]
method = pulse
source = auto

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7

[color]
gradient = 1

gradient_color_1 = '#89b4fa'
gradient_color_2 = '#74c7ec'
gradient_color_3 = '#94e2d5'
gradient_color_4 = '#a6e3a1'
gradient_color_5 = '#f9e2af'
gradient_color_6 = '#fab387'
gradient_color_7 = '#f38ba8'
gradient_color_8 = '#cba6f7'
EOF

pkill -f "cava -p $config_file"

cava -p "$config_file" | sed -u "$dict"