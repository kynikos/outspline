#!/usr/bin/env bash

version="0.8.3"
envdir="osenv"

if [ -d $envdir ]; then
  read -p "The $envdir directory already exists, remove it? [y|n]" -n 1 -s remove
  echo
  if [ $remove == "y" ]; then
    rm -rf $envdir
  else
    echo "Activate the virtualenv and execute outspline:"
    echo "  $ cd $envdir"
    echo "  $ ./bin/activate"
    echo "  $ ./bin/outspline --config ./outspline.conf"
    echo
    echo "Deactivate the virtualenv when done:"
    echo "  $ deactivate"
    exit 1
  fi
fi

if ! python2 -c "import wx" &> /dev/null; then
  echo "Install wxPython for this distribution."
  echo "  # pacman -S wxpython"
  exit 1
fi

if ! pacman -Q python2-gobject &> /dev/null; then
  echo "Install python2-gobject to support notifications:"
  echo "  # pacman -S python2-gobject"
  read -p "Continue without notifications? [y|n]" -n 1 -s cont
  echo
  if [ $cont != "y" ]; then
    exit 1
  fi
fi

virtualenv2 --system-site-packages $envdir

cd $envdir
source ./bin/activate

package="http://downloads.sourceforge.net/project/outspline/main/outspline-$version.tar.bz2"

curl -LO $package

tar xjf "outspline-$version.tar.bz2"
cd "outspline-$version"
../bin/python setup.py install --optimize=1
cd ..

# On the main system the icon cache may have to be refreshed
#gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor

# Also, without root rights, icons can't be installed in /usr/share/icons,
# therefore e.g. the tray icon doesn't appear

./bin/outspline --config ./outspline.conf

deactivate
