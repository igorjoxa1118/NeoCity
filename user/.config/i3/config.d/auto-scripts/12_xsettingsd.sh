#!/usr/bin/env bash
# Просто перезапускает xsettingsd для применения изменений, сделанных Theme.sh
pkill -x xsettingsd && xsettingsd &