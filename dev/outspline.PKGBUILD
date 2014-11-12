# Maintainer: Dario Giovannetti <dev at dariogiovannetti dot net>

pkgname='outspline'
pkgver='0.8.0'
pkgrel=1
pkgdesc="Outliner and personal time organizer to manage todo lists, schedule tasks, remind events."
arch=('any')
url="https://github.com/kynikos/outspline"
license=('GPL3')
depends=('wxpython<3.1')
optdepends=('outspline-extra: extra addons'
            'outspline-experimental: experimental addons'
            'outspline-development: development tools for beta testers'
            'python2-dbus: prevent opening multiple instances with the same configuration file'
            'dbus-glib: prevent opening multiple instances with the same configuration file'
            'libnotify: for desktop notifications (notify plugin)'
            'python2-gobject: for desktop notifications (notify plugin)')
conflicts=('organism' 'organism-organizer')
replaces=('organism' 'organism-organizer')
install=outspline.install
source=("http://downloads.sourceforge.net/project/kynikos/arch/$pkgname-$pkgver.tar.bz2")
sha256sums=('bba2cdeaef007e0ca63f0b1f4244114d65b7f74f67f1ebaf051e8ae5f0bbde12')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python2 setup.py install --root="$pkgdir" --optimize=1
}
