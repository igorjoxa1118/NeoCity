# Maintainer: vir0id

srcname=icons
pkgname=virOS-icons
pkgdesc='VirOS icons'
pkgver=1.3.2
pkgrel=1
arch=('any')
url="https://github.com/igorjoxa1118/virOS-icons"
license=('GPL')
makedepends=('git')
source=("git+$url.git")
sha256sums=('SKIP')

package() {
  cd ${srcdir}/${pkgname}/
  install -dm755 "${pkgdir}/usr/share/icons"

  cp -rf icons/. "${pkgdir}/usr/share/icons"
}
