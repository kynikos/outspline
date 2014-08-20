# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-development'
pkgver='0.6.0'
pkgrel=1
pkgdesc="Development component for Outspline"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
conflicts=('organism-development')
replaces=('organism-development')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('77e50f5a6f77c7ff20dcf33de0beedc160c0ea8c0ff54a26033b6c171b5818d8')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/,dbdeps/}__init__.py{,c,o}
}
