# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-development'
pkgver='0.8.0'
pkgrel=1
pkgdesc="Development component for Outspline"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
conflicts=('organism-development')
replaces=('organism-development')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('3277e25fe3a8e7112df953482949086fed184416e4c30c9223893ef2fb0b5137')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/extensions/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/plugins/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/components/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/info/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/info/extensions/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/info/plugins/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/conf/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/conf/extensions/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/conf/plugins/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/dbdeps/__init__.py{,c,o}
}
