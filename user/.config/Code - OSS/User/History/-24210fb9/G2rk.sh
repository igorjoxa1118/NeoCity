#!/bin/bash
#set -x 

size=$(du -hSc ~/.[^.]* | tail -n1 | awk '{print $1}')

echo "$size"