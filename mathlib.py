#MathLib.py

import types
import math
from decimal import Decimal

class MathLib:
    def __init__(self):
        self.constants = {}
        self.set_constant('true', True)
        self.set_constant('false', False)
        self.set_constant('pi', self.parse_number('3.14'))
        self.set_constant('kb', self.parse_number('0'))
        self.set_constant('Na', self.parse_number('6.02214e23'))
        self.set_constant('e', self.exp(1))
        self.set_constant('c', self.parse_number('3e8'))
        self.set_constant('c_e', self.parse_number('0'))        #electron properties
        self.set_constant('m_e', self.parse_number('0'))
        self.set_constant('c_p', self.parse_number('0'))        #proton properties
        self.set_constant('m_p', self.parse_number('0'))
        self.set_constant('c_n', self.parse_number('0'))        #neutron properties
        self.set_constant('m_n', self.parse_number('0'))

    def set_constant(self, name, val):
        self.constants[name] = val

    def get_constant(self, name):
        if name in  self.constants:
            return self.constants[name]
        else:
            return None

    def d(self, val):
        s = '%e' % val
        return Decimal(s)

    def parse_number(self, s):
        return Decimal(s)

    def format_number(self, n):
        if type(n) is types.BooleanType:
            if n:
                return 'True'
            else:
                return 'False'

        (sign, digits, exp) = n.as_tuple()
        if sign == '-':
            res = "-"
        else:
            res = ""
        int_len = len(digits) + exp
        disp_exp = math.floor(int_len / 3) * 3
        if disp_exp == 3:
            disp_exp = 0
        dot_pos = int_len - disp_exp
        for i in xrange(len(digits)):
            if i == dot_pos:
                if i == 0:
                    res += '0.'
                else:
                    res += '.'
            res += str(digits[i])
        if disp_exp != 0:
            res = res + 'e%d' % disp_exp

        return res

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
        return x / y

    def pow(self, x, y):
        if self.is_int(y):
            return x ** y
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
        return self.d(math.sin(x))

    def cos(self, x):
        return self.d(math.cos(x))

    def tan(self, x):
        return self.d(math.tan(x))

    def asin(self, x):
        return self.d(math.asin(x))

    def acos(self, x):
        return self.d(math.acos(x))

    def atan(self, x):
        return self.d(math.atan(x))

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
