#!/usr/bin/env python

import sys
import os.path


def main():
    for root, dirs, files in os.walk(sys.argv[1]):
        for file in files:
            if file.endswith(".pyc"):
                pyc = os.path.join(root, file)

                if not os.path.exists(pyc[:-1]):
                    os.remove(pyc)
                    print("Deleted {}".format(pyc))

if __name__ == '__main__':
    main()
