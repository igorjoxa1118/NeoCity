#About : simple script to show current song playing on cmus along with the progress icons
#Author: https://github.com/the-anonymous-raven

PLAY='󰎆 '
PAUSE='󰏤'

ICON_0PERC='󰝦'
ICON_10PERC='󰪞'
ICON_20PERC='󰪟'
ICON_30PERC='󰪟'
ICON_40PERC='󰪠'
ICON_50PERC='󰪡'
ICON_60PERC='󰪢'
ICON_70PERC='󰪣'
ICON_80PERC='󰪤'
ICON_90PERC='󰪥'
ICON_100PERC='󰪥'

get_length=$1

  song="$(cmus-remote -Q 2> /dev/null| awk -F/ NR==2'{print $NF}'|awk -F. '{print $1}')"
       if [[ "$song" == "" || "$song" == "set aaa_mode all" ]]; then
              echo " "
       else
              current_pos=$(cmus-remote -Q 2> /dev/null| grep "position" | awk '{print $2}')
              total_duration=$(cmus-remote -Q 2> /dev/null| grep "duration" | awk '{print $2}')

              #get a value out of 10 showing the progress of the music
              val=$(( $current_pos* 100/$total_duration ))
              round_val=$(( ($val + 10/2)/10 ))
              case $round_val in 
                0)
                  icon=$ICON_0PERC;;
                1)
                  icon=$ICON_10PERC;;
                2)
                  icon=$ICON_20PERC;;
                3)
                  icon=$ICON_30PERC;;
                4)
                  icon=$ICON_40PERC;;
                5)
                  icon=$ICON_50PERC;;
                6)
                  icon=$ICON_60PERC;;
                7)
                  icon=$ICON_70PERC;;
                8)
                  icon=$ICON_80PERC;;
                9)
                  icon=$ICON_90PERC;;
                10)
                  icon=$ICON_100PERC;;
                esac

        #song length trimmer
        if [[ -n $get_length && $get_length =~ ^[0-9]+$ ]]; then
            if [[ $(echo $song | wc -c) -gt $get_length ]]; then
                   song=$(echo $song| head -c $get_length)
                   song="$song..."
            fi
        fi

        #return string
              is_playing=$(cmus-remote -Q 2> /dev/null | awk -F" " NR==1'{print $NF}')
              if [[ "$is_playing" = "playing" ]]; then
                     playing="$PLAY $song $icon"
              elif [[ "$is_playing" = "paused" ]]; then
                     playing="$PAUSE $song $icon"
              fi
       fi
       
       echo "$playing"