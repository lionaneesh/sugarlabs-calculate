# rational.py, rational number class Reinier Heeres <reinier@heeres.eu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Change log:
#    2007-07-03: rwh, first version

import types
from decimal import Decimal

import logging
_logger = logging.getLogger('Rational')

from gettext import gettext as _

class Rational:

    def __init__(self, n=None, d=None):
        self.n = 0
        self.d = 0

        if n is not None:
            self.set(n, d)

    def set(self, n, d=None):
        if d is not None:
            self.n = long(n)
            self.d = long(d)
        elif type(n) is types.TupleType or type(n) is types.ListType:
            self.n = long(rval[0])
            self.d = long(rval[1])
        elif type(n) == types.StringType:
            return

        self._simplify()

    def __str__(self):
        if self.d == 1 or self.d == 0:
            return "%d" % (self.n)
        else:
            return "%d/%d" % (self.n, self.d)
           
    def __float__(self):
        return float(self.n) / float(self.d)

    def gcd(self, a, b):
        if b == 0:
            return a
        else:
            return self.gcd(b, a % b)

    def _simplify(self):
        if self.d == 0:
            return

        if self.n == self.d:
            self.n = long(1)
            self.d = long(1)
        else:
            gcd = self.gcd(self.n, self.d)
            self.n /= gcd
            self.d /= gcd

    def __add__(self, rval):
        if isinstance(rval, Rational):
            ret = Rational(self.n * rval.d + self.d * rval.n, self.d * rval.d)
        elif type(rval) is types.IntType or type(rval) is types.LongType:
            ret = Rational(self.n + self.d * rval, self.d)
        else:
            ret = float(self) + rval
        return ret

    def __radd__(self, lval):
        return self.__add__(lval)

    def __sub__(self, rval):
        if isinstance(rval, Rational):
            ret = Rational(self.n * rval.d - self.d * rval.n, self.d * rval.d)
        elif type(rval) is types.IntType or type(rval) is types.LongType:
            ret = Rational(self.n - self.d * rval, self.d)
        else:
            ret = float(self) - rval
        return ret

    def __rsub__(self, lval):
        return -self.__sub__(lval)

    def __mul__(self, rval):
        if isinstance(rval, Rational):
            ret = Rational(self.n * rval.n, self.d * rval.d)
        elif type(rval) is types.IntType or type(rval) is types.LongType:
            ret = Rational(self.n * rval, self.d)
        elif isinstance(rval, Decimal):
            ret = rval * Decimal(str(float(self)))
        else:
            ret = rval * float(self)
        return ret

    def __rmul__(self, lval):
        return self.__mul__(lval)

    def __div__(self, rval):
        if isinstance(rval, Rational):
            ret = Rational(self.n * rval.d, self.d * rval.n)
        elif type(rval) is types.IntType or type(rval) is types.LongType:
            ret = Rational(self.n, self.d * rval)
        else:
            ret = float(self) / rval
        return ret

    def __rdiv__(self, lval):
        return self.__div__(lval)

    def __neg__(self):
        return Rational(-self.n, self.d)

    def __abs__(self):
        self.n = abs(self.n)
        self.d = abs(self.d)

    def __pow__(self, rval):
        if type(rval) is types.IntType or type(rval) is types.LongType:
            ret = Rational(self.n ** rval, self.d ** rval)
        else:
            ret = float(self.n) ** rval / float(self.d) ** rval

        return ret
