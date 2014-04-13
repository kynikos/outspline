# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-experimental'
pkgver='0.5.0'
pkgrel=1
pkgdesc="Experimental addons for Outspline"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('f33108bb4a5be62ea662dc7fa15fee107cfad4f2a045a669bf76d6394a483018')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/}__init__.py{,c,o}
}
