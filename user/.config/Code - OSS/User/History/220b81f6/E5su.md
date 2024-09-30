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
click-left = "$HOME/.local/bin/Search-Tube/mpv-youtube-playlist.sh" &
click-right = "$HOME/.local/bin/Search-Tube/mpv-youtube-kill.sh" &
```

```python
[module/mpv]
type = custom/script
exec-if = pidof mpv 
exec = "$HOME/.local/bin/Search-Tube/mpv-zscroll.sh"
tail = true
click-left = echo 'cycle pause' | socat - /tmp/mpv_socket
click-right = "$HOME/.local/bin/Search-Tube/mpv-youtube-kill.sh"
scroll-up = "$HOME/.local/bin/Search-Tube/polybar-mpv/mpv.sh" --volume-up
scroll-down = "$HOME/.local/bin/Search-Tube/polybar-mpv/mpv.sh" --volume-down
```

```python
[module/mpv-prev]
type = custom/script
exec-if = pidof mpv
exec = echo " "
click-left = echo 'playlist-prev' | socat - /tmp/mpv_socket
```

```python
[module/mpv-next]
type = custom/script
exec-if = pidof mpv
exec = echo " "
click-left = echo 'playlist-next' | socat - /tmp/mpv_socket
```
Polybar config.ini

```python
modules-left = mpv mpv-prev mpv-next
modules-center = mpv-youtube-icon
modules-right = 
```