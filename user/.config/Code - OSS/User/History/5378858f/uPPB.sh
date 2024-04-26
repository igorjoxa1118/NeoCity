#!/bin/bash

#set -x 
# Для памяти -aAEHSXxr
if [ "$(id -u)" != 0 ]; then
    echo "Необходимы права суперпользователя" >&2
	exit 1
fi

today=$(date +"%Y-%m-%d-%I-%M-%p")
LOCALROOT="/" 
SYSTAR="sys.tar.gz"
BACKUPFOLDER="/backup"
ROOTFOLDER="backup/root"
HOMEFOLDER="backup/home"

update='pacman -Sy git pv rclone rsync dialog du'

backuppaths=("/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/lost+found")

DIALOG() {
username=$(dialog --stdout --title "Пользователь, чъя копия будет создана?" --inputbox "Имя пользвателя:" 14 48)
FULLBACKUP=$(dialog --stdout --title "Все пути должны начинаться и заканчиваться "/" " --inputbox "Куда сделать резервную копию?:" 14 48)
GOOGLEDRIVE=$(dialog --stdout --title "Перед использованием настройте rclone " --inputbox "Имя вашего облачного диска(Без :)?:" 14 48)
homedir="/home/$username"

if [ -z $username ]; then
   DIALOG
   elif [ -z $FULLBACKUP ]; then
   DIALOG
   elif [ -z $GOOGLEDRIVE ]; then
   DIALOG
   fi
}

FOLDERBACKUPSEARCH=$(rclone lsd $GOOGLEDRIVE:/ | grep backup | awk '{print $5}')
DRIVE_TAR_DELL=$(rclone ls $GOOGLEDRIVE:$BACKUPFOLDER | grep $SYSTAR | awk '{print $2}')
LOCALTAR=$(ls -al $FULLBACKUP | grep sys.tar.gz | awk '{print $9}')
TAR_SIZE=$(du -s $FULLBACKUP$FOLDERS | awk '{print $1}')

MENUDRIVE() {

BACKTITLE="v.1.0"
MENU="Выберене нужный пункт:"
HEIGHT=30
WIDTH=60
CHOICE_HEIGHT=20

OPTIONS=(1 "Синхронизировать домашний каталог"
         2 "Создать резервную копию root+home"
         3 "Удалить резервные копии"
         4 "Создать архив sys.tar.gz"
         5 "Записать архив sys.tar.gz в Drive"
         6 "Извлечь архив в /"
         7 "Установка программного обеспечения")

CHOICE=$(dialog --clear \
                --backtitle "$BACKTITLE" \
                --title "$TITLE" \
                --menu "$MENU" \
                $HEIGHT $WIDTH \
                $CHOICE_HEIGHT \
                "${OPTIONS[@]}" \
                2>&1 >/dev/tty)

clear
case $CHOICE in
"1" )
              if dialog --yesno "Уверены?" 0 0; then 
              rsync -aAEHSXxr --exclude=".cache/mozilla/*" $homedir.[^.]* $FULLBACKUP | dialog --infobox "Я не завис, процесс идет. Ждите!" 3 34
              dialog --title "Сообщение!" --msgbox "\n Домашний каталог синхронизирован!" 6 50
              MENUDRIVE
              else 
	            MENUDRIVE
              fi
;;

"2" )
            if dialog --yesno "Уверены?" 0 0; then
              if ! [[ -d $FULLBACKUP ]]; then                                 # Если не существует папки "Ваш путь", то...
	                mkdir $FULLBACKUP                                       # Создай папку "Ваш путь"
	            

              elif ! [[ -d "$FULLBACKU$PROOTFOLDER" ]]; then             # Если не существует папки "Ваш путь"/backup/root
                    mkdir -p $FULLBACKUP$ROOTFOLDER                        # Создай папку "Ваш путь"/backup/root
					          rm -rf /var/cache/pacman/pkg/*.pkg.*
                    rsync -aAEHSXxr --exclude={"${backuppaths[@]}"} / $FULLBACKUP$ROOTFOLDER | dialog --infobox "Я не завис, процесс идет. Ждите!" 3 34 # Запиши копии "/" в "Ваш путь"/backup/root               
                        if ! [[ -d "$FULLBACKUP$ROOTFOLDER/home/$username" ]]; then		                # Если не существует папки "Ваш путь"/backup, то ...
	                        mkdir -p $FULLBACKUP$ROOTFOLDER/home/$username                        # Создай папки "Ваш путь"/backup и "Ваш путь"/home 
                          rsync -aAEHSXxr --exclude=".cache/mozilla/*" /home/$username/.[^.]* $FULLBACKUP$ROOTFOLDER/home/$username | dialog --infobox "Я не завис, процесс идет. Ждите!" 3 34
                        elif [[ -d $FULLBACKUP$ROOTFOLDER/home/$username ]]; then
                          rsync -aAEHSXxr --exclude=".cache/mozilla/*" /home/$username/.[^.]* $FULLBACKUP$ROOTFOLDER/home/$username | dialog --infobox "Я не завис, процесс идет. Ждите!" 3 34
                        fi
                          dialog --title "Сообщение!" --msgbox "\n Копирование выполнено" 6 50
                          MENUDRIVE                                               
			        else
                    dialog --title "Ошибка!" --msgbox "\n Что-то пошло не так" 6 50
		                MENUDRIVE
              fi
            else
            MENUDRIVE
            fi
;;


"3" )         
              if dialog --yesno "Уверены?" 0 0; then
               if [ `ls $FULLBACKUP | wc -l` -gt 0 ]; then # Если каталог не пуст
                rm -rf $FULLBACKUP* | dialog --infobox "Удаление резервных копий!" 3 34
                dialog --title "Сообщение!" --msgbox "\n Все копии удалены" 6 50
                else
                dialog --title "Сообщение!" --msgbox "\n Каталог пуст" 6 50
               fi
                MENUDRIVE
              else
              MENUDRIVE
              fi
;;

"4" )
            if dialog --yesno "Уверены?" 0 0; then
              cd $FULLBACKUP$FOLDERS
              if [[ -f $SYSTAR ]]; then
              rm $SYSTAR
              else
              #tar -czvpf $FULLBACKUP$today$SYSTAR .
              cd $ROOTFOLDER
              tar --exclude={"${backuppaths[@]}"} -czpf - * | (pv -n --size $(ls -laR $FULLBACKUP$FOLDERS$ROOTFOLDER | wc | awk '{print $3}') > $FULLBACKUP$today.sys.tar.gz) 2>&1 | dialog --gauge "Пакую в архив... Ждите!" 10 70              
              dialog --title "Сообщение!" --msgbox "\n Резервная копия успешно создана" 6 50
              fi
              MENUDRIVE
            else
              MENUDRIVE
            fi
;;

"5" ) 
            if dialog --yesno "Уверены?" 0 0; then
              if ! [[ $GOOGLEDRIVE:$BACKUPFOLDER ]]; then 
                  rclone mkdir $GOOGLEDRIVE:$BACKUPFOLDER/
              elif [[ -z $DRIVE_TAR_DELL ]]; then  # Если строка пуста (нет архива) то...
                  rclone deletefile $GOOGLEDRIVE:$BACKUPFOLDER/$DRIVE_TAR_DELL # Удали ту строку (архив)
                  rclone copy --progress --copy-links $FULLBACKUP*$SYSTAR $GOOGLEDRIVE:$BACKUPFOLDER/
                  dialog --title "Сообщение!" --msgbox "\n Архив записан в Drive" 6 50
                  MENUDRIVE
              fi
            fi
;;

"6" ) 
                if dialog --yesno "Уверены?" 0 0; then
                 if [[ $LOCALTAR == *"sys.tar.gz"* ]]; then
                   tar -xf $FULLBACKUP*$SYSTAR -C $LOCALROOT | dialog --infobox "Я не завис, процесс идет. Ждите!" 3 34
                   dialog --title "Сообщение!" --msgbox "\n Файлы скопированы в /" 6 50
                   MENUDRIVE
                 else
                   dialog --title "Сообщение!" --msgbox "\n Что-то пошло не так" 6 50
                   MENUDRIVE
                 fi
                fi
;;

"7" ) 

                  ${update}
                  MENUDRIVE
;;
     esac
} 

DIALOG
MENUDRIVE