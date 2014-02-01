# wxClasses
# Copyright (C) 2013-2014 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of wxClasses.
#
# wxClasses is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wxClasses is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with wxClasses.  If not, see <http://www.gnu.org/licenses/>.


import functools
import inspect


class Protected(object):
    # Derive all existing classes from object *******************************************
    # Test with subclasses **************************************************************
    # Test with iterations/recursions ***************************************************
    # Test manipulation of private lists or dictionaries ********************************
    # Enable only for debugging? ********************************************************
    def __init__(self):
        stack = inspect.stack()
        print('111', stack[1][0], stack[-2][0])  # **************************************
        # Maybe it's not necessary to store __FRAME *************************************
        object.__setattr__(self, '__FRAME', stack[-2][0])

    def __getattribute__(self, name):
        stack = inspect.stack(0)
        attr = object.__getattribute__(self, name)
        print('GET', name)#, stack[1][0], stack[-2][0])  # ********************************
        for d in dir(attr):
            print('DIR', d, getattr(attr, d))
        for frame in stack:
            print('FRAME', frame)
            print(inspect.getframeinfo(frame[0]))

        if object.__getattribute__(self, '__FRAME') is stack[1][0] or \
                                            hasattr(attr, '_PUBLIC_METHOD'):
            return attr
        else:
            raise PrivateMethodError()

    def __setattr__(self, name, value):
        stack = inspect.stack()
        print('SET', name, stack[1][0], stack[-2][0])  # ********************************
        attr = object.__getattribute__(self, name)

        if object.__getattribute__(self, '__FRAME') is stack[1][0] or \
                                            hasattr(attr, '_PUBLIC_METHOD'):
            object.__setattr__(self, name, value)
        else:
            raise PrivateMethodError()

    def __delattr__(self, name):
        stack = inspect.stack()
        print('DEL', name, stack[1][0], stack[-2][0])  # ********************************
        attr = object.__getattribute__(self, name)

        if object.__getattribute__(self, '__FRAME') is stack[1][0] or \
                                            hasattr(attr, '_PUBLIC_METHOD'):
            object.__delattr__(self, name)
        else:
            raise PrivateMethodError()


class PrivateMethodError(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def public(function):
    # The outer function (public) is executed only *once* when defining the
    # class, *not* every time it's instantiated (which is a good thing)
    function._PUBLIC_METHOD = True
    #function._AAA = True  # ************************************************************

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        print('FUNC', inspect.getmembers(function))  # ***********************************************
        function._AAA = 'AAA'  # *********************************************************
        return function(*args, **kwargs)

    return wrapper


# ***************************************************************************************
class Test(Protected):
    def __init__(self):
        frame = inspect.currentframe()
        print('000', frame)
        Protected.__init__(self)

        print('SSS', self.call())
        print('TTT', self._call())
        print('TT2', self.call2())
        print('TT3', self.call3())

    def _call(self):
        return ':('

    @public
    def call(self):
        return ':)'

    def call2(self):
        return self.call()

    def call3(self):
        return self.call2()


class Test2(Test):
    def __init__(self):
        Test.__init__(self)

        print('TT4', self.call4())

    def call4(self):
        return self.call3()


class Test3(object):
    def __init__(self):
        self.test0 = Test()
        self.test4 = Test2()

        print('TT5', self.call1())
        print('TT6', self.call2())
        print('TT7', self.call3())

    def call1(self):
        return self.test0.call()

    def call2(self):
        return self.test0._call()

    def call3(self):
        return self.test4.call4()

test1 = Test()
test2 = Test()
test3 = Test2()
test4 = Test3()

print('UUU', test1.call())
print('VVV', test1._call())
print('WWW', test2.call())
print('XXX', test2._call())
print('YYY', test3.call())
print('ZZZ', test3._call())
