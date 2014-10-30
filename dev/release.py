#!/usr/bin/env python

import sys
import os
import shutil
import subprocess
import re

import configfile

# This script is supposed to be run in the ./dev directory as ./release.py
# If the -l option is passed, the external libraries won't be bundled and will
#  have to be installed on the system separately
# It's possible to build only some components by specifying them as arguments
#  for the command

if len(sys.argv) > 1 and sys.argv[1] == "-l":
    BUNDLE_LIBS = False
    COMPONENTS = sys.argv[2:]
else:
    BUNDLE_LIBS = True
    COMPONENTS = sys.argv[1:]

ROOT_DIR = '..'
DEST_DIR = '.'
SRC_DIR = os.path.join(ROOT_DIR, 'src')
BASE_DIR = os.path.join(SRC_DIR, 'outspline')
SCRIPTS_DIR = os.path.join(SRC_DIR, 'scripts')
DATA_DIR = os.path.join(SRC_DIR, 'data_files')
DEPS_DIR = os.path.join(BASE_DIR, 'dbdeps')
RDATA_DIR = os.path.join(BASE_DIR, "data")
PACKAGES = {
    'main': 'outspline',
    'development': 'outspline-development',
    'organism': 'outspline-organism',
    'experimental': 'outspline-experimental',
}

def main():
    if len(COMPONENTS) > 0:
        for cname in COMPONENTS:
            cfile = cname + '.component'
            make_component_package(cfile, cname)
            make_pkgbuild_package(cname)

    else:
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
    datadir = os.path.join(pkgdir, 'data_files')
    depsdir = os.path.join(maindir, 'dbdeps')
    rdatadir = os.path.join(maindir, 'data')

    os.makedirs(maindir)
    shutil.copy2(os.path.join(ROOT_DIR, 'LICENSE'), pkgdir)
    shutil.copy2(os.path.join(SRC_DIR, 'setup.py'), pkgdir)
    shutil.copy2(os.path.join(SRC_DIR, pkgname + '.config.py'),
                                            os.path.join(pkgdir, 'config.py'))
    shutil.copy2(os.path.join(BASE_DIR, cfile), maindir)
    shutil.copy2(os.path.join(BASE_DIR, '__init__.py'), maindir)

    os.makedirs(datadir)
    os.makedirs(rdatadir)

    os.makedirs(depsdir)
    shutil.copy2(os.path.join(DEPS_DIR, '__init__.py'), depsdir)

    if component.get_bool('provides_core', fallback='false'):
        shutil.copytree(os.path.join(BASE_DIR, 'core'), os.path.join(
                            maindir, 'core'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
        shutil.copytree(os.path.join(BASE_DIR, 'coreaux'), os.path.join(
                            maindir, 'coreaux'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))

        try:
            shutil.copytree(os.path.join(BASE_DIR, 'static'), os.path.join(
                            maindir, 'static'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
        except shutil.Error as errs:
            # A symlink to a folder has been found (an external library)
            if BUNDLE_LIBS:
                for srcname, dstname, exception in errs.args[0]:
                    shutil.copytree(os.path.join(BASE_DIR, 'static',
                            os.readlink(srcname)), dstname,
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
            else:
                for srcname, dstname, exception in errs.args[0]:
                    with open(dstname + ".py", "w") as file_:
                        file_.write("from __future__ import absolute_import\n"
                                                "from {} import *\n".format(
                                                os.path.basename(dstname)))

        for file_ in ('core_api.py', 'coreaux_api.py', 'outspline.conf'):
            shutil.copy2(os.path.join(BASE_DIR, file_), maindir)

        shutil.copytree(SCRIPTS_DIR, os.path.join(pkgdir, 'scripts'))
        make_data_files("core", datadir, rdatadir)

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

            make_data_files(os.path.join(type_, addon), datadir, rdatadir)

            if type_ == 'extensions':
                try:
                    shutil.copy2(os.path.join(DEPS_DIR, addon + '.py'),
                                                                    depsdir)
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


def make_data_files(rpath, datadir, rdatadir):
    try:
        shutil.copytree(os.path.join(DATA_DIR, rpath), os.path.join(datadir,
                                                                        rpath))
    except FileNotFoundError:
        pass

    try:
        shutil.copytree(os.path.join(RDATA_DIR, rpath), os.path.join(rdatadir,
                                                                        rpath))
    except FileNotFoundError:
        pass


def make_pkgbuild_package(cname):
    pkgname = PACKAGES[cname]
    pkgbuild = os.path.join(DEST_DIR, pkgname + '.PKGBUILD')

    subprocess.call(["updpkgsums", pkgbuild])

    tmppkgbuild = os.path.join(DEST_DIR, 'PKGBUILD')
    shutil.copy2(pkgbuild, tmppkgbuild)

    subprocess.call(["mkaurball", ])
    # Don't call makepkg --clean or errors will happen

    os.remove(tmppkgbuild)


if __name__ == '__main__':
    main()
