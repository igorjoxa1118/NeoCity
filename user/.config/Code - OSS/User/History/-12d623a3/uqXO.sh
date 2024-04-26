#!/bin/sh
# $Id: yesno,v 1.9 2010/01/14 01:11:11 tom Exp $

. ./setup/setup-vars-welcome.sh

DIALOG_ERROR=254
export DIALOG_ERROR

$DIALOG --title "Привет мир!" --clear "$@" \
        --yesno "Привет! Этот скрипт позволит тебе: \n
1.Смонтировать раздел в папку Загрузки домашнего каталога \n
2.Смонтировать USB_BACKUP накопитель в папку Загрузки смонтированного ранее раздела  \n
3.Удалить старые файлы Skel из домашнего каталога \n
4.Установить файлы Skel из примонтированного USB_BACKUP накопителя" 15 61

retval=$?

. ./setup/report-welcome.sh
