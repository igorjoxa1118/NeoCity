#!/bin/sh
##
# cmus-notify -- based on cmus-status-display
# author: nblock <nblock [at] archlinux [dot] us>
# version: git
# license: GPLv2
##
# a simple script to display cmus' status inside awesome with awesome-client
#
# in cmus: ":set status_display_program=/path/to/cmus-notify" to activate the script
##

output()
{
  local start="cmuswidget:set_markup(\"<span foreground='orange'>music: </span><span foreground='#00FF00'>"
  local end='</span>")'
  local clean=$(echo "$*" |sed -e 's/[<>&]*//g')
  echo "${start}${clean}${end}" | awesome-client 2>&1
}

while test $# -ge 2
do
	eval _$1='$2'
	shift
	shift
done

if test -n "$_file"
then
	h=$(($_duration / 3600))
	m=$(($_duration % 3600))

	duration=""
	test $h -gt 0 && dur="$h:"
	duration="$dur$(printf '%02d:%02d' $(($m / 60)) $(($m % 60)))"

  if [ -z "$_date" ]; then
    output "[$_status] $_artist - $_title - $_album [$duration]"
  else
    output "[$_status] $_artist - $_title - $_album ($_date) [$duration]"
  fi
elif test -n "$_url"
then
	output "[$_status] $_url - $_title"
else
	output "[$_status]"
fi