# Search-Tube

Polybar module for i3

```python
[module/mpv-youtube-icon]
type = custom/text
content = " "
content-font = 0
content-background = ${color.background}
content-foreground = ${color.foreground_blue}
content-padding = 0
click-left = "$HOME/.config/i3/scripts/polybar-mpv/mpv-youtube-playlist.sh" &
click-right = "$HOME/.config/i3/scripts/polybar-mpv/mpv-youtube-kill.sh" &
```

```python
[module/mpv]
type = custom/script
exec-if = pidof mpv 
exec = ~/.config/i3/scripts/polybar-mpv/mpv-zscroll.sh
tail = true
click-left = echo 'cycle pause' | socat - /tmp/mpv_socket
click-right =  ~/.config/i3/scripts/mpv-youtube-kill.sh
scroll-up = ~/.config/i3/scripts/polybar-mpv/mpv.sh --volume-up
scroll-down = ~/.config/i3/scripts/polybar-mpv/mpv.sh --volume-down
format-foreground = ${color.foreground_blue}
format-background = ${color.background}
format-underline = ${color.foreground_blue}
```

```python
[module/mpv-prev]
type = custom/script
exec-if = pidof mpv
exec = echo " "
click-left = echo 'playlist-prev' | socat - /tmp/mpv_socket
format-foreground = ${color.foreground_blue}
format-background = ${color.background}
```

```python
[module/mpv-next]
type = custom/script
exec-if = pidof mpv
exec = echo " "
click-left = echo 'playlist-next' | socat - /tmp/mpv_socket
format-foreground = ${color.foreground_blue}
format-background = ${color.background}
```
Polybar config.ini

```python
modules-left = mpv mpv-prev mpv-next
modules-center = mpv-youtube-icon
modules-right = 
```