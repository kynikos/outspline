# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-experimental'
pkgver='0.2.0'
pkgrel=1
pkgdesc="Experimental addons for Outspline"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
install="$pkgname.install"
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('d9e499f41f61c10e7b9e2e49f2724c96e1b4744f7cc9bbde1e93d8d387511337')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/}__init__.py{,c,o}
}
