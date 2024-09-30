#!/bin/bash
#set -x

PWD="$(pwd)"

I3="$HOME/.config/i3"
POLYBAR="$HOME/.config/polybar"
ROFI="$HOME/.config/rofi"
PICOM="$HOME/.config/picom.conf"
DUNST="$HOME/.config/dunst"
GTK2="$HOME/.config/gtk-2.0"
GTK3="$HOME/.config/gtk-3.0"
XFCE4="$HOME/.config/xfce4"
HOME_gtk2="$HOME/.gtkrc-2.0"
HOME_zshrc="$HOME/.zshrc"

BAK_DIR="$HOME/.config/config_bak"
user="$(whoami)"

mkdir -p "$BAK_DIR/home"

main_function() {

if [[ ! -f /usr/bin/autotiling ]]; then
cd $PWD/sources/autotiling
   makepkg -s
   cd ..
   fi

if [[ ! -d /usr/share/oh-my-zsh ]]; then
cd $PWD/sources/oh-my-zsh-git
   if [[ -f "$PWD/oh-my-zsh-git/PKGBUILD" ]]; then
   makepkg -s
   fi
   cd ..
  else
    echo "Somting wrong"
fi

if [[ ! -f /usr/bin/oh-my-posh ]] || [[ ! -f /usr/local/bin/oh-my-posh ]]; then
  if [[ -f "$PWD/sources/oh-my-posh-bin/PKGBUILD" ]]; then
   cd $PWD/sources/oh-my-posh-bin/
    makepkg -s

else
   wget https://github.com/JanDeDobbeleer/oh-my-posh/releases/latest/download/posh-linux-amd64 -O /usr/local/bin/oh-my-posh
   sudo chmod +x /usr/local/bin/oh-my-posh
   cd ../..
   fi
fi
 
for dir in $I3 $POLYBAR $ROFI $DUNST $GTK2 $GTK3 $XFCE4 $PICOM # Перечисляем каталоги в переменную "dir"

do if [[ -d $dir ]] || [[ -f $PICOM ]]; then # Делать, если существуют или каталоги
  mv $dir $BAK_DIR
  fi
done

for dir in $HOME_gtk2 $HOME_zshrc  # Перечисляем каталоги в переменную "dir"

do if [[ -f $dir ]]; then # Делать, если существуют или файлы
  mv $dir $BAK_DIR/home
  fi
done

cd $PWD
      makepkg -s
}

if main_function;  then 
               cd $PWD
               sudo pacman -U *.zst
               sudo pacman -S dialog cmus xfce4-terminal thunar polybar rofi dunst nitrogen fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-history-substring-search zsh-syntax-highlighting starship
               sudo chown -R $user:$user $HOME/.local
  else
   sudo rm -r $BAK_DIR
   exit 1;
fi
