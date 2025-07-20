#!/bin/sh

nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk '{ print "GPU",""$1""}' | sed 's/....//'
#nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,nounits,noheader | sed 's/\\([0-9]\\+\\), \\([0-9]\\+\\)/\\1%  \\2°C/g'