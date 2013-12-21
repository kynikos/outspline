# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline'
pkgver='0.3.0'
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
sha256sums=('2592ec8f5e37033d3093381e80dac5dae9e29fb8c33be150a79bd852cc3e1189')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
}
