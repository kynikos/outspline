# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-development'
pkgver='1.0.0pb1'
pkgrel=2
pkgdesc="Development component for Outspline (PRE-BETA!)"
arch=('any')
url="https://github.com/kynikos/outspline-development"
license=('GPL3')
depends=('outspline')
source=("http://www.dariogiovannetti.net/files/$pkgname-$pkgver.tar.gz")
md5sums=('3a1efa3de8014fbb020b22ac2c3150d1')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --prefix="/usr" --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/}__init__.py{,c,o}
}
