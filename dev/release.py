#!/usr/bin/env python

# This script is supposed to be run in the ./dev directory as ./release.py
# If the -l option is passed, the external libraries won't be bundled and will
#  have to be installed on the system separately
# It's possible to build only some components by specifying them as arguments
#  for the command

import sys
import os
import shutil
import pkgutil
import imp

ROOT_DIR = '..'
DEST_DIR = '.'
SRC_DIR = os.path.join(ROOT_DIR, 'src')
BASE_DIR = os.path.join(SRC_DIR, 'outspline')
SCRIPTS_DIR = os.path.join(SRC_DIR, 'scripts')
DATA_DIR = os.path.join(SRC_DIR, 'data_files')
COMPONENTS_DIR = os.path.join(BASE_DIR, 'components')
INFO_DIR = os.path.join(BASE_DIR, 'info')
CONF_DIR = os.path.join(BASE_DIR, 'conf')
DEPS_DIR = os.path.join(BASE_DIR, 'dbdeps')
RDATA_DIR = os.path.join(BASE_DIR, "data")

PACKAGES = {
    'main': 'outspline',
    'extra': 'outspline-extra',
    'development': 'outspline-development',
    'experimental': 'outspline-experimental',
}


def main(cliargs, action=None):
    if len(cliargs) > 1 and cliargs[1] == "-l":
        BUNDLE_LIBS = False
        COMPONENTS = cliargs[2:]
    else:
        BUNDLE_LIBS = True
        COMPONENTS = cliargs[1:]

    if len(COMPONENTS) > 0:
        for cname in COMPONENTS:
            _build_component(cname, bundle_libs=BUNDLE_LIBS, action=action)

    else:
        for module_loader, cname, ispkg in pkgutil.iter_modules((
                                                            COMPONENTS_DIR, )):
            _build_component(cname, bundle_libs=BUNDLE_LIBS, action=action)


def _build_component(cname, bundle_libs, action):
    pkgname = PACKAGES[cname]
    _make_component_package(cname, pkgname, bundle_libs)

    if action:
        action(pkgname)


def _make_component_package(cname, pkgname, bundle_libs):
    cfile = os.path.join(COMPONENTS_DIR, cname + ".py")
    component = imp.load_source(cname, cfile)

    pkgver = component.version
    pkgdirname = pkgname + '-' + pkgver
    pkgdir = os.path.join(DEST_DIR, pkgdirname)
    maindir = os.path.join(pkgdir, 'outspline')
    datadir = os.path.join(pkgdir, 'data_files')
    componentsdir = os.path.join(maindir, 'components')
    infodir = os.path.join(maindir, 'info')
    confdir = os.path.join(maindir, 'conf')
    depsdir = os.path.join(maindir, 'dbdeps')
    rdatadir = os.path.join(maindir, 'data')

    os.makedirs(maindir)
    shutil.copy2(os.path.join(ROOT_DIR, 'LICENSE'), pkgdir)
    shutil.copy2(os.path.join(SRC_DIR, 'setup.py'), pkgdir)
    shutil.copy2(os.path.join(SRC_DIR, pkgname + '.config.py'),
                                            os.path.join(pkgdir, 'config.py'))
    shutil.copy2(os.path.join(BASE_DIR, '__init__.py'), maindir)

    os.makedirs(componentsdir)
    shutil.copy2(os.path.join(COMPONENTS_DIR, '__init__.py'), componentsdir)
    shutil.copy2(cfile, componentsdir)

    os.makedirs(datadir)
    os.makedirs(rdatadir)

    os.makedirs(infodir)
    shutil.copy2(os.path.join(INFO_DIR, '__init__.py'), infodir)

    os.makedirs(confdir)
    shutil.copy2(os.path.join(CONF_DIR, '__init__.py'), confdir)

    os.makedirs(depsdir)
    shutil.copy2(os.path.join(DEPS_DIR, '__init__.py'), depsdir)

    try:
        assert component.provides_core
    except (AttributeError, AssertionError):
        pass
    else:
        shutil.copytree(os.path.join(BASE_DIR, 'core'), os.path.join(
                            maindir, 'core'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
        shutil.copytree(os.path.join(BASE_DIR, 'coreaux'), os.path.join(
                            maindir, 'coreaux'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))

        shutil.copy2(os.path.join(INFO_DIR, "core.py"), infodir)
        shutil.copy2(os.path.join(CONF_DIR, "core.py"), confdir)

        try:
            shutil.copytree(os.path.join(BASE_DIR, 'static'), os.path.join(
                            maindir, 'static'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
        except shutil.Error as errs:
            # A symlink to a folder has been found (an external library)
            if bundle_libs:
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

        for file_ in ('core_api.py', 'coreaux_api.py'):
            shutil.copy2(os.path.join(BASE_DIR, file_), maindir)

        shutil.copytree(SCRIPTS_DIR, os.path.join(pkgdir, 'scripts'),
                            ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
        _copy_data_files("core", datadir, rdatadir)

    for type_ in ("extensions", "interfaces", "plugins"):
        try:
            addons = getattr(component, type_)
        except AttributeError:
            pass
        else:
            typedir = os.path.join(maindir, type_)
            os.mkdir(typedir)
            shutil.copy2(os.path.join(BASE_DIR, type_, '__init__.py'), typedir)

            typeinfodir = os.path.join(infodir, type_)
            os.mkdir(typeinfodir)
            shutil.copy2(os.path.join(INFO_DIR, type_, '__init__.py'),
                                                                typeinfodir)

            typeconfdir = os.path.join(confdir, type_)
            os.mkdir(typeconfdir)
            shutil.copy2(os.path.join(CONF_DIR, type_, '__init__.py'),
                                                                typeconfdir)

            for addon in addons:
                shutil.copy2(os.path.join(INFO_DIR, type_, addon + '.py'),
                                                                typeinfodir)

                shutil.copy2(os.path.join(CONF_DIR, type_, addon + '.py'),
                                                                typeconfdir)

                try:
                    shutil.copy2(os.path.join(BASE_DIR, type_, addon +
                                                        '_api.py'), typedir)
                except FileNotFoundError:
                    pass

                _copy_data_files(os.path.join(type_, addon), datadir, rdatadir)

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


def _copy_data_files(rpath, datadir, rdatadir):
    try:
        shutil.copytree(os.path.join(DATA_DIR, rpath), os.path.join(datadir,
                    rpath), ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
    except FileNotFoundError:
        pass

    try:
        shutil.copytree(os.path.join(RDATA_DIR, rpath), os.path.join(rdatadir,
                    rpath), ignore=shutil.ignore_patterns('*.pyc', '*.pyo'))
    except FileNotFoundError:
        pass


if __name__ == '__main__':
    main(sys.argv)
