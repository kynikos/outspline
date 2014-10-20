# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-organism'
pkgver='0.7.0'
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
sha256sums=('3611f21ddd7813686ec3a031cecdf0840789d6fff5db980bbb38ddd03d8251bf')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,extensions/,plugins/,dbdeps/}__init__.py{,c,o}
}
