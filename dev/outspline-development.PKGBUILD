# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-development'
pkgver='0.2.1'
pkgrel=1
pkgdesc="Development component for Outspline"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
conflicts=('organism-development')
replaces=('organism-development')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('aa7b846a1d8b74221420f2e7fe5b639dfdacf30ee19cd072f40276ceb6ee4072')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/}__init__.py{,c,o}
}
