#!/usr/bin/env bash

check ()
{
    while pkill offlineimap
    do
        sleep 2
    done
}

quick ()
{
    offlineimap -u quiet -q -s
}

full ()
{
    offlineimap -u quiet -s
}

# parse options
while getopts "qf" OPTION
do
    case $OPTION in
        q)
            check
            quick
            exit 0
            ;;
        f)
            check
            full
            exit 0
            ;;
        ?)
            echo "Nothing to do."
            exit 1
            ;;
    esac
done
