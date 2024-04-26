pkgname=Search-Tube
pkgver=1.0
pkgrel=1
pkgdesc='Search for your favorite music. Play your favorite playlists'
url="https://github.com/igorjoxa1118/Search-Tube"
arch=("any")
license=("GPL")
makedepends=('git')

depends=("yad")

source=("git+${url}.git")
sha256sums=('SKIP')

package() {
   
   local="$HOME/.local/bin/Search-Tube"

  install -dm755 "${pkgdir}/usr/share/applications"
  install -dm755 "${pkgdir}/$HOME/.local/bin/Search-Tube"
  cd ${srcdir}/${pkgname}

  sed -i -e "s|Exec=sh /home/eddy/.config/i3/scripts/polybar-mpv/mpv-youtube-playlist.sh|Exec=sh '$local'/mpv-youtube-playlist.sh|g" scripts/search-tube.desktop
  sed -i -e "s|Icon=/home/eddy/.config/i3/scripts/polybar-mpv/icons/youtube.svg|Icon='$local'/youtube.svg|g" scripts/search-tube.desktop
  sed -i -e "s|Path=/home/eddy/.config/i3/scripts/polybar-mpv/|Path='$local'|g" scripts/search-tube.desktop

  cp -r scripts/*.sh ${pkgdir}/$HOME/.local/bin/Search-Tube
  cp -r scripts/search-tube.desktop ${pkgdir}/usr/share/applications
}