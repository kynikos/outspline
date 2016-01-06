#!/usr/bin/env python

# This script is supposed to be run in the ./dev directory as ./release-arch.py
# If the -l option is passed, the external libraries won't be bundled and will
#  have to be installed on the system separately
# It's possible to build only some components by specifying them as arguments
#  for the command

import sys
import os
import shutil
import subprocess

import release


def _make_pkgbuild(pkgname):
    pkgbuild = os.path.join(release.DEST_DIR, pkgname + '.PKGBUILD')

    subprocess.call(["updpkgsums", pkgbuild])

    tmppkgbuild = os.path.join(release.DEST_DIR, 'PKGBUILD')
    shutil.copy2(pkgbuild, tmppkgbuild)

    subprocess.call(["makepkg", "--source", "--clean"])

    os.remove(tmppkgbuild)


if __name__ == '__main__':
    release.main(sys.argv, _make_pkgbuild)
