# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-organism'
pkgver='0.2.1'
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
sha256sums=('36dd26a0faead47064d3dc0b5201108ec970d19d2ba03f330ed82fb52a571f35')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/}__init__.py{,c,o}
}
