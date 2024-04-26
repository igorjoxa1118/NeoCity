#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

function deleted () {
    rm -rf /home/"$username"/.*
}

deleted