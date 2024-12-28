#!/bin/sh

nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk '{ print "GPU",""$1""}'
