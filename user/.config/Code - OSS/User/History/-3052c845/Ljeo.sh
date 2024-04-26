#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

function deleted () {
    #rm /home/"$username"/test/.*
    echo $(pwd)
}