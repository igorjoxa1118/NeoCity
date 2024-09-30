#!/usr/bin/bash

yad --geometry=20x40+500+400 \
--fontname="Arial Bold 15" \
--wrap --justify="center" \
--margins=1 \
--tail \
--editable \
--fore=green \
--back=yellow \
--listen \
--auto-close \
--auto-kill \
--monitor \
--text-info </tmp/tempo.txt &
##  based on-->: https://www.mankier.com/1/yad#Options-Text_info_options

for i in {1..5};do
		echo $i >/tmp/tempo.txt
		sleep 3
done