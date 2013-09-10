# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-organism'
pkgver='0.2.0'
pkgrel=1
pkgdesc="Organizer component for Outspline, adding advanced time management abilities"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
conflicts=('organism-organizer')
replaces=('organism-organizer')
install="$pkgname.install"
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('33803cb89861e1ebf1180bfdef2aff427d71305d458838aa557c2a1c28842545')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/}__init__.py{,c,o}
}
