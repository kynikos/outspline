# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline'
pkgver='1.0.0pb1'
pkgrel=2
pkgdesc="A highly modular and extensible outliner for managing your notes (PRE-BETA!)"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('wxpython'
         'python2-configfile'
         'python2-texthistory'
         'python2-plural')
optdepends=('outspline-organism: adds personal organizer capabilities'
            'outspline-development: development tools for beta testers')
install="$pkgname.install"
source=("http://www.dariogiovannetti.net/files/$pkgname-$pkgver.tar.gz")
md5sums=('a243d18c2900312634c205278c25239f')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --prefix="/usr" --root="$pkgdir" --optimize=1
}
