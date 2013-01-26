# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='organism-tk'
pkgver='0.1'
pkgrel=2
pkgdesc="Tk component for Organism."
arch=('any')
url="https://github.com/kynikos/organism-tk"
license=('GPL3')
depends=('organism')
install=organism-tk.install
source=("http://www.dariogiovannetti.net/files/$pkgname-$pkgver.tar.bz2")
md5sums=('92077b8c68f9543619bca607757e49a0')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --prefix="/usr" --root="$pkgdir" --optimize=1
    rm $pkgdir/usr/lib/python2.7/site-packages/organism/{,interfaces/}__init__.py{,c,o}
}
