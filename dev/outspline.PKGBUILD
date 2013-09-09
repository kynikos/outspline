# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline'
pkgver='0.2.0'
pkgrel=1
pkgdesc="Highly modular and extensible outliner for managing your notes"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('wxpython'
         'python2-configfile'
         'python2-texthistory'
         'python2-plural')
optdepends=('outspline-organism: adds personal organizer capabilities'
            'outspline-development: development tools for beta testers')
conflicts=('organism')
replaces=('organism')
install="$pkgname.install"
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('a243d18c2900312634c205278c25239fa243d18c2900312634c205278c25239f')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
}
