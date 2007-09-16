# MathLib.py, generic math library wrapper by Reinier Heeres <reinier@heeres.eu>
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
import math
from decimal import Decimal
import random

import logging
_logger = logging.getLogger('MathLib')

class MathLib:
    ANGLE_DEG = math.pi/180
    ANGLE_RAD = 1
    ANGLE_GRAD = 1

    def __init__(self):
        self.constants = {}
        self.set_angle_type(self.ANGLE_DEG)

#Constants should maybe become variables in eqnparser.py
        self.set_constant('true', True)
        self.set_constant('false', False)
        self.set_constant('pi', self.parse_number('3.1415926535'))
        self.set_constant('kb', self.parse_number('1.380650524e-23'))
        self.set_constant('Na', self.parse_number('6.02214e23'))
        self.set_constant('e', self.exp(1))
        self.set_constant('c', self.parse_number('2.99792458e8'))
        self.set_constant('c_e', self.parse_number('-1.60217648740e-19'))       #electron properties
        self.set_constant('m_e', self.parse_number('9.109382616e-31'))
        self.set_constant('c_p', self.parse_number('1.6021765314e-19'))         #proton properties
        self.set_constant('m_p', self.parse_number('1.6726217129e-27'))
        self.set_constant('c_n', self.parse_number('0'))                        #neutron properties
        self.set_constant('m_n', self.parse_number('1.6749272928e-27'))

    def set_angle_type(self, type):
        self.angle_scaling = self.d(type)
        _logger.debug('Angle type set to:%s', self.angle_scaling)

    def set_constant(self, name, val):
        self.constants[name] = val

    def get_constant(self, name):
        if name in  self.constants:
            return self.constants[name]
        else:
            return None

    def d(self, val):
        s = '%.10e' % val
        d = Decimal(s)
        return d.normalize()

    def parse_number(self, s):
        return Decimal(s)

    def format_number(self, n):
        if type(n) is types.BooleanType:
            if n:
                return 'True'
            else:
                return 'False'
        elif type(n) is types.StringType:
            return n
        elif type(n) is types.NoneType:
            return 'Error'
        elif type(n) is types.IntType:
            n = self.d(n)
        elif type(n) is types.FloatType:
            n = self.d(n)
        elif not isinstance(n, Decimal):
            return 'Error: unsupported type'
        (sign, digits, exp) = n.as_tuple()
        if len(digits) > 9:
            exp += len(digits) - 9
            digits = digits[:9]

        if sign:
            res = "-"
        else:
            res = ""
        int_len = len(digits) + exp
        
        if int_len == 0:
            if exp < -5:
                disp_exp = exp + len(digits) 
            else:
                disp_exp = 0
        elif 0 < int_len < 6:
            disp_exp = 0
        else:
            disp_exp = int_len - 1
        
        dot_pos = int_len - disp_exp
        for i in xrange(len(digits)):
            if i == dot_pos:
                if i == 0:
                    res += '0.'
                else:
                    res += '.'
            res += str(digits[i])

        if len(digits) < dot_pos:
            for i in xrange(len(digits), dot_pos):
                res += '0'

        if disp_exp != 0:
            res = res + 'e%d' % disp_exp

        return res

    def short_format(self, n):
        ret = self.format_number(n)
        if len(ret) > 7:
            ret = "%1.1e" % n
        return ret

    def is_int(self, n):
        (sign, d, e) = n.normalize().as_tuple()
        return e == 0

    def is_float(self, n):
        if isinstance(n, Decimal):
            return not self.is_int(n)
        else:
            return False

    def is_bool(self, n):
        return type(n) is types.BoolType

    def compare(self, x, y):
        return x == y

    def negate(self, x):
        return -x

    def abs(self, x):
        return self.d(math.fabs(x))

    def add(self, x, y):
        return x + y

    def sub(self, x, y):
        return x - y

    def mul(self, x, y):
        return x * y

    def div(self, x, y):
        if y == 0:
            return None
        else:
            return x / y

    def pow(self, x, y):
        if self.is_int(y):
            return x ** int(y)
        else:
            return self.d(math.pow(x, y))

    def sqrt(self, x):
        return self.d(math.sqrt(x))

    def mod(self, x, y):
        if self.is_int(y):
            return x % y
        else:
            return self.d(0)

    def exp(self, x):
        return self.d(math.exp(x))

    def ln(self, x):
        if x > 0:
            return self.d(math.log(x))
        else:
            return 0

    def log10(self, x):
        if x > 0:
           return self.d(math.log10(x))
        else:
            return 0

    def factorial(self, n):
        if not self.is_int(n):
            return self.d(0)

        res = n
        while n > 2:
            res *= n - 1
            n -= 1
        return res

    def sin(self, x):
        return self.d(math.sin(x * self.angle_scaling))

    def cos(self, x):
        return self.d(math.cos(x * self.angle_scaling))

    def tan(self, x):
        return self.d(math.tan(x * self.angle_scaling))

    def asin(self, x):
        return self.d(math.asin(x)) / self.angle_scaling

    def acos(self, x):
        return self.d(math.acos(x)) / self.angle_scaling

    def atan(self, x):
        return self.d(math.atan(x)) / self.angle_scaling

    def sinh(self, x):
        return self.d(math.sinh(x))

    def cosh(self, x):
        return self.d(math.cosh(x))

    def tanh(self, x):
        return self.d(math.tanh(x))

    def asinh(self, x):
        return self.d(math.asinh(x))

    def acosh(self, x):
        return self.d(math.acosh(x))

    def atanh(self, x):
        return self.d(math.atanh(x))

    def round(self, x):
        return self.d(round(x))

    def floor(self, x):
        return self.d(math.floor(x))

    def ceil(self, x):
        return self.d(math.ceil(x))

    def rand_float(self):
        return self.d(random.random())

    def rand_int(self):
        return self.d(random.randint(0, 65535))

    def shift_left(self, x, y):
        if self.is_int(x) and self.is_int(y):
            return self.d(int(x) << int(y))
        else:
            return 0

    def shift_right(self, x, y):
        if self.is_int(x) and self.is_int(y):
            return self.d(int(x) >> int(y))
        else:
            return 0

    def factorize(self, x):
        if not self.is_int(x):
            return 0

        factors = []
        num = x
        i = 2
        while i <= math.sqrt(num):
            if num % i == 0:
                factors.append(i)
                num /= i
                i = 2
            elif i == 2:
                i += 1
            else:
                i += 2
        factors.append(num)

        if len(factors) == 1:
            return "1 * %d" % x
        else:
            str = "%d" % factors[0]
            for fac in factors[1:]:
                str += " * %d" % fac
            return str
