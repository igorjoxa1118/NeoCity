#! /bin/bash

bar="▁▂▃▄▅▆▇█"
dict="s/;//g;"

# creating "dictionary" to replace char with bar
i=0
while [ $i -lt ${#bar} ]
do
    dict="${dict}s/$i/${bar:$i:1}/g;"
    i=$((i=i+1))
done

# write cava config
config_file="$HOME/.config/cava/config"
echo "
[general]
bars = 10

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7

[color]
background = '#1e1e2e'

gradient = 1

gradient_color_1 = '#94e2d5'
gradient_color_2 = '#89dceb'
gradient_color_3 = '#74c7ec'
gradient_color_4 = '#89b4fa'
gradient_color_5 = '#cba6f7'
gradient_color_6 = '#f5c2e7'
gradient_color_7 = '#eba0ac'
gradient_color_8 = '#f38ba8'
" > $config_file

# read stdout from cava
cava -p $config_file | while read -r line; do
    echo $line | sed $dict
done
