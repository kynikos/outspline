# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-experimental'
pkgver='0.4.0'
pkgrel=1
pkgdesc="Experimental addons for Outspline"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('a77049f02645b0d08ed7cee9ce5d8766dba0ae26d229ac3bcd3e52ea4046bf1e')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/}__init__.py{,c,o}
}
