# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline'
pkgver='0.6.0'
pkgrel=1
pkgdesc="Highly modular and extensible outliner for managing your notes"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('wxpython<3.1'
         'python2-configfile'
         'python2-texthistory'
         'python2-plural')
optdepends=('outspline-organism: adds personal organizer capabilities'
            'outspline-development: development tools for beta testers'
            'python2-dbus: prevent opening multiple instances with the same configuration file'
            'dbus-glib: prevent opening multiple instances with the same configuration file')
conflicts=('organism')
replaces=('organism')
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('b9fa82dcb7cdd732486e128ef700b07c5714ea04ac8de5c318a2575cb40a82d0')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
}
