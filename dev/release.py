#!/usr/bin/env python

import os
import shutil
import subprocess
import re

import configfile

# This script is supposed to be run in the ./dev directory as ./release.py
ROOT_DIR = '..'
DEST_DIR = '.'
SRC_DIR = os.path.join(ROOT_DIR, 'src')
BASE_DIR = os.path.join(SRC_DIR, 'outspline')
PACKAGES = {
    'main': 'outspline',
    'development': 'outspline-development',
    'organism': 'outspline-organism',
}

def main():
    for cfile in os.listdir(BASE_DIR):
        cname, ext = os.path.splitext(cfile)

        if ext == '.component':
            make_component_package(cfile, cname)
            make_pkgbuild_package(cname)


def make_component_package(cfile, cname):
    component = configfile.ConfigFile(os.path.join(BASE_DIR, cfile),
                                                          inherit_options=False)
    pkgname = PACKAGES[cname]
    pkgver = component['version']
    pkgdirname = pkgname + '-' + pkgver
    pkgdir = os.path.join(DEST_DIR, pkgdirname)
    maindir = os.path.join(pkgdir, 'outspline')

    os.makedirs(maindir)
    shutil.copy2(os.path.join(ROOT_DIR, 'LICENSE'), pkgdir)
    shutil.copy2(os.path.join(SRC_DIR, pkgname + '.setup.py'),
                                               os.path.join(pkgdir, 'setup.py'))
    shutil.copy2(os.path.join(BASE_DIR, cfile), maindir)
    shutil.copy2(os.path.join(BASE_DIR, '__init__.py'), maindir)

    if component.get_bool('provides_core', fallback='false'):
        for src, dest, sd in ((SRC_DIR, pkgdir, 'files'),
                              (BASE_DIR, maindir, 'core'),
                              (BASE_DIR, maindir, 'coreaux')):
            shutil.copytree(os.path.join(src, sd), os.path.join(dest, sd),
                                ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))

        for file_ in ('core_api.py', 'coreaux_api.py', 'outspline.conf'):
            shutil.copy2(os.path.join(BASE_DIR, file_), maindir)

    addons = find_addons(component)

    for type_ in addons:
        typedir = os.path.join(maindir, type_)
        os.mkdir(typedir)
        shutil.copy2(os.path.join(BASE_DIR, type_, '__init__.py'), typedir)

        for caddon in addons[type_]:
            addon, version = caddon

            shutil.copy2(os.path.join(BASE_DIR, type_, addon + '.conf'),
                                                                        typedir)

            try:
                shutil.copy2(os.path.join(BASE_DIR, type_, addon + '_api.py'),
                                                                        typedir)
            except FileNotFoundError:
                pass

            shutil.copytree(os.path.join(BASE_DIR, type_, addon),
                                                   os.path.join(typedir, addon),
                                ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))

    shutil.make_archive(pkgdir, 'bztar', base_dir=pkgdirname)
    shutil.rmtree(pkgdir)


def find_addons(component):
    addons = {}

    for o in component:
        if o[:9] == 'extension':
            try:
                addons['extensions']
            except KeyError:
                addons['extensions'] = [component[o].split(' '), ]
            else:
                addons['extensions'].append(component[o].split(' '))
        elif o[:9] == 'interface':
            try:
                addons['interfaces']
            except KeyError:
                addons['interfaces'] = [component[o].split(' '), ]
            else:
                addons['interfaces'].append(component[o].split(' '))
        elif o[:6] == 'plugin':
            try:
                addons['plugins']
            except KeyError:
                addons['plugins'] = [component[o].split(' '), ]
            else:
                addons['plugins'].append(component[o].split(' '))

    return addons


def make_pkgbuild_package(cname):
    pkgname = PACKAGES[cname]
    pkgbuild = os.path.join(DEST_DIR, pkgname + '.PKGBUILD')
    tmppkgbuild = os.path.join(DEST_DIR, 'PKGBUILD')

    shutil.copy2(pkgbuild, tmppkgbuild)

    p = subprocess.Popen(["makepkg", "--geninteg", "--clean"],
                                                         stdout=subprocess.PIPE)
    out = p.communicate()[0].decode("utf-8")

    with open(pkgbuild, 'r') as f:
        r = f.read()
        ur = re.sub('sha256sums\=\(\'[a-z0-9]+\'\)\n', out, r)

    with open(pkgbuild, 'w') as f:
        f.write(ur)

    with open(tmppkgbuild, 'w') as f:
        f.write(ur)

    subprocess.call(["makepkg", "--source", "--clean"])

    os.remove(tmppkgbuild)


if __name__ == '__main__':
    main()
