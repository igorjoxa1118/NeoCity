#!/bin/bash

#####################################
#                                   #
#  @author      : 00xWolf           #
#    GitHub    : @mmsaeed509       #
#    Developer : Mahmoud Mohamed   #
#  﫥  Copyright : Exodia OS         #
#                                   #
#####################################

# you can run script with 2 arguments (your commit comment)
# ./push.sh -m "yourCommit"
#

# a simple script to push your commits to GitHub #

# get branch name (e.g master, main, etc... ) #
Branch=$(git branch --show-current)
DEFAULT_COMMIT_MSG=$(git status -s)

echo -e "\n${BRed}[*] Your Current Branch : ${BYellow}${Branch}${RESET_COLOR}"

# get new updates if it founded #
echo -e "\n${BPurple}[+] Updating Repo... \n${RESET_COLOR}"
git pull 

echo -e "\n${BPurple}[+] The new changes in the repo:- \n${RESET_COLOR}"
git status -s

echo -e "\n${BPurple}[+] Adding new changes to the repo... \n${RESET_COLOR}"
git add --all .

if [ "$1" == "-m" ];
    
    then
        
        # commit changes#
        echo ""
        git commit -m "$2"

else

    # use the default commit msg #
    echo ""
    git commit -m "updated/added ${DEFAULT_COMMIT_MSG}"

fi

# push to repo #
echo ""
git push -u origin $Branch

# D O N E! #
echo -e "\n${BGreen}[✔] D O N E \n${RESET_COLOR}"