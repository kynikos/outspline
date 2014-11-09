# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-organism'
pkgver='0.7.1'
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
install=outspline-organism.install
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('4e24179ceab6e825b8ae620f3945002559d497f676a9f1c939a7df99a1e83ca0')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/extensions/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/plugins/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/components/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/info/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/info/extensions/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/info/interfaces/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/info/plugins/__init__.py{,c,o}
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/dbdeps/__init__.py{,c,o}
}
