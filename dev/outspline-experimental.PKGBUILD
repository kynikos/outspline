# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-experimental'
pkgver='0.7.0'
pkgrel=1
pkgdesc="Experimental addons for Outspline"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('56e52ca8398323b75f7da187b30772fb3fbb0e0fb01b34e95cf1b23f87b6b565')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/,dbdeps/}__init__.py{,c,o}
}
