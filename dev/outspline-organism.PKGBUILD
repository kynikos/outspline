# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-organism'
pkgver='0.6.0'
pkgrel=1
pkgdesc="Organizer component for Outspline, adding advanced time management abilities"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
optdepends=('libnotify: for desktop notifications (notify plugin)'
            'python2-gobject: for desktop notifications (notify plugin)')
conflicts=('organism-organizer')
replaces=('organism-organizer')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('1ada9c1b447fcec59ea903455f7212c1352d258edf3e16782d0623c484e1ffdf')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/,dbdeps/}__init__.py{,c,o}
}
