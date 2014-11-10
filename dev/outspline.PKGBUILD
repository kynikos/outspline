# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline'
pkgver='0.7.1'
pkgrel=1
pkgdesc="Highly modular and extensible outliner for managing your notes"
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('wxpython<3.1')
optdepends=('outspline-organism: adds personal organizer capabilities'
            'outspline-development: development tools for beta testers'
            'python2-dbus: prevent opening multiple instances with the same configuration file'
            'dbus-glib: prevent opening multiple instances with the same configuration file')
conflicts=('organism')
replaces=('organism')
install=outspline.install
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('20a4465bbba554652c1e3c8483802b3e626607dc0253b7883dbcb5e4621c3a5e')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
}
