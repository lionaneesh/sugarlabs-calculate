# -*- coding: UTF-8 -*-
# mathlib.py, generic math library wrapper by Reinier Heeres <reinier@heeres.eu>
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
import inspect
import math
from decimal import Decimal
from rational import Rational
import random

import logging
_logger = logging.getLogger('MathLib')

from gettext import gettext as _
import locale

# Python 2.5 does not have a binary formatter built-in
# This requires a function b10bin() to interpret the result
def format_bin(n):
    bits = ''
    while n > 0:
        if n & 1:
            bits = '1' + bits
        else:
            bits = '0' + bits
        n >>= 1

    return 'b10bin(%s)' % bits

try:
    _BIN = bin
except:
    _BIN = format_bin

class MathLib:
    ANGLE_DEG = math.pi/180
    ANGLE_RAD = 1
    ANGLE_GRAD = 1

    FORMAT_EXPONENT = 1
    FORMAT_SCIENTIFIC = 2

    def __init__(self):
        self.set_format_type(self.FORMAT_SCIENTIFIC)
        self.set_digit_limit(9)
        self.set_chop_zeros(True)
        self.set_integer_base(10)

        self._setup_i18n()

    def _setup_i18n(self):
        loc = locale.localeconv()

        # The separator to mark thousands (default: ',')
        self.thousand_sep = loc['thousands_sep']
        if self.thousand_sep == "" or self.thousand_sep == None:
            self.thousand_sep = ","

        # The separator to mark fractions (default: '.')
        self.fraction_sep = loc['decimal_point']
        if self.fraction_sep == "" or self.fraction_sep == None:
            self.fraction_sep = "."

        # TRANS: multiplication symbol (default: '×')
        self.mul_sym = _('mul_sym')
        if len(self.mul_sym) == 0 or len(self.mul_sym) > 3:
            self.mul_sym = '×'

        # TRANS: division symbol (default: '÷')
        self.div_sym = _('div_sym')
        if len(self.div_sym) == 0 or len(self.div_sym) > 3:
            self.div_sym = '÷'

        # TRANS: equal symbol (default: '=')
        self.equ_sym = _('equ_sym')
        if len(self.equ_sym) == 0 or len(self.equ_sym) > 3:
            self.equ_sym = '='

    def set_format_type(self, fmt, digit_limit=9):
        self.format_type = fmt
        _logger.debug('Format type set to %s', fmt)

    def set_integer_base(self, base):
        if base not in (2, 8, 10, 16):
            _logger.warning('Unsupported integer base requested')
            return False
        self.integer_base = base
        _logger.debug('Integer base set to %s', base)

    def set_digit_limit(self, digits):
        self.digit_limit = digits
        _logger.debug('Digit limit set to %s', digits)

    def set_chop_zeros(self, chop):
        self.chop_zeros = bool(chop)
        _logger.debug('Chop zeros set to %s', self.chop_zeros)

    def d(self, val):
        if isinstance(val, Decimal):
            return val
        elif type(val) in (types.IntType, types.LongType):
            return Decimal(val)
        elif type(val) == types.StringType:
            d = Decimal(val)
            return d.normalize()
        elif type(val) is types.FloatType or hasattr(val, '__float__'):
            s = '%.18e' % float(val)
            d = Decimal(s)
            return d.normalize()
        else:
            return None

    def parse_number(self, s):
        s = s.replace(self.fraction_sep, '.')

        try:
            d = Decimal(s)
            if self.is_int(d):
                return int(d)
            else:
                return Decimal(s)
        except Exception, inst:
            return None

    _BASE_FUNC_MAP = {
        2: _BIN,
        8: oct,
        16: hex,
    }
    def format_int(self, n, base=None):
        if base is None:
            base = self.integer_base
        ret = self._BASE_FUNC_MAP[base](long(n))
        return ret.rstrip('L')

    def format_decimal(self, n):
        if self.chop_zeros:
            n = n.normalize()
        (sign, digits, exp) = n.as_tuple()
        if len(digits) > self.digit_limit:
            exp += len(digits) - self.digit_limit
            digits = digits[:self.digit_limit]
        if len(digits) < self.digit_limit:
            exp -= self.digit_limit - len(digits)
            digits += (0,) * (self.digit_limit - len(digits))
            print exp, digits
        if sign:
            res = "-"
        else:
            res = ""
        int_len = len(digits) + exp

        if int_len == 0:
            if exp < -self.digit_limit:
                disp_exp = exp + len(digits) 
            else:
                disp_exp = 0
        elif -self.digit_limit < int_len < self.digit_limit:
            disp_exp = 0
        else:
            disp_exp = int_len - 1

        dot_pos = int_len - disp_exp

#        _logger.debug('len(digits) %d, exp: %d, int_len: %d, disp_exp: %d, dot_pos: %d', len(digits), exp, int_len, disp_exp, dot_pos)

        if dot_pos < 0:
            res = '0' + self.fraction_sep
            for i in xrange(dot_pos, 0):
                res += '0'

        for i in xrange(len(digits)):
            if i == dot_pos:
                if i == 0:
                    res += '0' + self.fraction_sep
                else:
                    res += self.fraction_sep
            res += str(digits[i])

        if int_len > 0 and len(digits) < dot_pos:
            for i in xrange(len(digits), dot_pos):
                res += '0'

        if disp_exp != 0:
            if self.format_type == self.FORMAT_EXPONENT:
                res = res + 'e%d' % disp_exp
            elif self.format_type == self.FORMAT_SCIENTIFIC:
                res = res + u'×10**%d' % disp_exp

        return res

    def format_number(self, n):
        if type(n) is types.BooleanType:
            if n:
                return 'True'
            else:
                return 'False'
        elif type(n) is types.StringType:
            return n
        elif type(n) is types.UnicodeType:
            return n
        elif type(n) is types.NoneType:
            return _('Undefined')
        elif type(n) is types.IntType:
            n = self.d(n)
        elif type(n) is types.FloatType:
            n = self.d(n)
        elif type(n) is types.LongType:
            n = self.d(n)
        elif isinstance(n, Rational):
            n = self.d(Decimal(n.n) / Decimal(n.d))
        elif not isinstance(n, Decimal):
            return _('Error: unsupported type')

        if self.is_int(n) and self.integer_base != 10:
            return self.format_int(n)
        else:
            return self.format_decimal(n)

    def short_format(self, n):
        ret = self.format_number(n)
        if len(ret) > 7:
            ret = "%1.1e" % n
        return ret

    def is_int(self, n):
        if type(n) is types.IntType or type(n) is types.LongType:
            return True

        if not isinstance(n, Decimal):
            n = self.d(n)
            if n is None:
                return False

        (sign, d, e) = n.normalize().as_tuple()
        return e >= 0

if __name__ == "__main__":
    ml = MathLib()
    val = 0.99999999999999878
    print 'is_int(%.18e): %s' % (val, ml.is_int(val))
    # Beyond float precision
    val = 0.999999999999999999
    print 'is_int(%.18e): %s' % (val, ml.is_int(val))
    val = ml.d(0.99999999999999878)**2
    print 'is_int(%s): %s' % (val, ml.is_int(val))
    vals = ('0.1230', '12.340', '0.0123', '1230', '123.0', '1.230e17')
    for valstr in vals:
        val = Decimal(valstr)
        print 'Formatted value: %s (from %s)' % (ml.format_number(val), valstr)
    for base in (2, 8, 16):
        print 'Format 252 in base %d: %s' % (base, ml.format_int(252, base))

