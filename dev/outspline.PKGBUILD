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
sha256sums=('795ed0ff40885675cbf5f6d88e0a6af2b97b6b63ad04729d099b60e8a543625a')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
}
