# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline-tk'
pkgver='0.1.0'
pkgrel=1
pkgdesc="Tk component for Outspline."
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('outspline')
install=outspline-tk.install
source=("http://www.dariogiovannetti.net/files/$pkgname-$pkgver.tar.bz2")
md5sums=('92077b8c68f9543619bca607757e49a0')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --prefix="/usr" --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/outspline/{,interfaces/}__init__.py{,c,o}
}
