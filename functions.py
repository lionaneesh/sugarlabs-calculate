# functions.py, functions available in Calculate,
# by Reinier Heeres <reinier@heeres.eu>
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

# Any variable or function in this module that does not start with an
# underscore ('_') will be available in Calculate through astparser.py.
# Docstrings will automatically be added to the help index for that function.
# However, instead of setting the docstring on a function in the simple way we
# add it after the function definition so that they can more easily be
# localized through gettext.

import types
import math
import random
from decimal import Decimal as _Decimal
from rational import Rational as _Rational

from gettext import gettext as _

# List of functions to allow translating the function names.
_FUNCTIONS = [
    _('add'),
    _('abs'),
    _('acos'),
    _('acosh'),
    _('asin'),
    _('asinh'),
    _('atan'),
    _('atanh'),
    _('and'),
    _('b10bin'),
    _('ceil'),
    _('cos'),
    _('cosh'),
    _('div'),
    _('gcd'),
    _('exp'),
    _('factorial'),
    _('fac'),
    _('factorize'),
    _('floor'),
    _('inv'),
    _('is_int'),
    _('ln'),
    _('log10'),
    _('mul'),
    _('or'),
    _('rand_float'),
    _('rand_int'),
    _('round'),
    _('sin'),
    _('sinh'),
    _('sinc'),
    _('sqrt'),
    _('sub'),
    _('square'),
    _('tan'),
    _('tanh'),
    _('xor'),
    ]    

def _d(val):
    '''Return a _Decimal object.'''

    if isinstance(val, _Decimal):
        return val
    elif type(val) in (types.IntType, types.LongType):
        return _Decimal(val)
    elif type(val) == types.StringType:
        d = _Decimal(val)
        return d.normalize()
    elif type(val) is types.FloatType or hasattr(val, '__float__'):
        s = '%.18e' % float(val)
        d = _Decimal(s)
        return d.normalize()
    else:
        return None

class ClassValue:
    """
    Class to share a value with the outside world.
    This is required because plain floats / integers are not asigned by
    reference, and can therefore not easily be changed in a different place.
    """
    def __init__(self, val):
        self.value = val

angle_scaling = ClassValue(1.0)

def _scale_angle(x):
    return x * angle_scaling.value

def _inv_scale_angle(x):
    return x / angle_scaling.value

def abs(x):
    return math.fabs(x)
abs.__doc__ = _(
'abs(x), return absolute value of x, which means -x for x < 0')

def acos(x):
    return _inv_scale_angle(math.acos(x))
acos.__doc__ = _(
'acos(x), return the arc cosine of x. This is the angle for which the cosine \
is x. Defined for -1 <= x < 1')

def acosh(x):
    return math.acosh(x)
acosh.__doc__ = _(
'acosh(x), return the arc hyperbolic cosine of x. This is the value y for \
which the hyperbolic cosine equals x.')

def And(x, y):
    return x & y
And.__doc__ = _(
'And(x, y), logical and. Returns True if x and y are True, else returns False')

def add(x, y):
    if isinstance(x, _Decimal) or isinstance(y, _Decimal):
        x = _d(x)
        y = _d(y)
    return x + y
add.__doc__ = _('add(x, y), return x + y')

def asin(x):
    return _inv_scale_angle(math.asin(x))
asin.__doc__ = _(
'asin(x), return the arc sine of x. This is the angle for which the sine is x. \
Defined for -1 <= x <= 1')

def asinh(x):
    return math.asinh(x)
asinh.__doc__ = _(
'asinh(x), return the arc hyperbolic sine of x. This is the value y for \
which the hyperbolic sine equals x.')

def atan(x):
    return _inv_scale_angle(math.atan(x))
atan.__doc__ = _(
'atan(x), return the arc tangent of x. This is the angle for which the tangent \
is x. Defined for all x')

def atanh(x):
    return math.atanh(x)
atanh.__doc__ = _(
'atanh(x), return the arc hyperbolic tangent of x. This is the value y for \
which the hyperbolic tangent equals x.')

def b10bin(x):
    ret = 0
    while x > 0:
        ret <<= 1

        y = x % 10
        if y == 1:
            ret += 1
        elif y != 0:
            raise ValueError(_('Number does not look binary in base 10'))

        x /= 10

    return ret

b10bin.__doc__ = _(
'b10bin(x), interpret a number written in base 10 as binary, e.g.: \
b10bin(10111) = 23,')

def ceil(x):
    return math.ceil(float(x))
ceil.__doc__ = _('ceil(x), return the smallest integer larger than x.')

def cos(x):
    return math.cos(_scale_angle(x))
cos.__doc__ = _(
'cos(x), return the cosine of x. This is the x-coordinate on the unit circle \
at the angle x')

def cosh(x):
    return math.cosh(x)
cosh.__doc__ = _(
'cosh(x), return the hyperbolic cosine of x. Given by (exp(x) + exp(-x)) / 2')

def div(x, y):
    if y == 0 or y == 0.0:
        raise ValueError(_('Can not divide by zero'))

    if is_int(x) and float(abs(x)) < 1e12 and \
            is_int(y) and float(abs(y)) < 1e12:
        return _Rational(x, y)

    if isinstance(x, _Decimal) or isinstance(y, _Decimal):
        x = _d(x)
        y = _d(y)

    return x / y

def _do_gcd(a, b):
    if b == 0:
        return a
    else:
        return _do_gcd(b, a % b)

def gcd( a, b):
    TYPES = (types.IntType, types.LongType)
    if type(a) not in TYPES or type(b) not in TYPES:
        raise ValueError(_('Invalid argument'))
    return _do_gcd(a, b)
gcd.__doc__ = _(
'gcd(a, b), determine the greatest common denominator of a and b. \
For example, the biggest factor that is shared by the numbers 15 and 18 is 3.')

def exp(x):
    return math.exp(float(x))
exp.__doc__ = _('exp(x), return the natural exponent of x. Given by e^x')

def factorial(n):
    if type(n) not in (types.IntType, types.LongType):
        raise ValueError(_('Factorial only defined for integers'))

    if n == 0:
        return 1

    n = long(n)
    res = long(n)
    while n > 2:
        res *= n - 1
        n -= 1

    return res
factorial.__doc__ = _(
'factorial(n), return the factorial of n. \
Given by n * (n - 1) * (n - 2) * ...')

def fac(x):
    return factorial(x)
fac.__doc__ = _(
'fac(x), return the factorial of x. Given by x * (x - 1) * (x - 2) * ...')

def factorize(x):
    if not is_int(x):
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
        ret = "%d" % factors[0]
        for fac in factors[1:]:
            ret += " * %d" % fac
        return ret
factorize.__doc__ = (
'factorize(x), determine the prime factors that together form x. \
For examples: 15 = 3 * 5.')

def floor(x):
    return math.floor(float(x))
floor.__doc__ = _('floor(x), return the largest integer smaller than x.')

def inv(x):
    return 1 / x
inv.__doc__ = _('inv(x), return the inverse of x, which is 1 / x')

def is_int(n):
    if type(n) in (types.IntType, types.LongType):
        return True

    if isinstance(n, _Rational):
        return (n.n == 0 or n.d == 1)

    if not isinstance(n, _Decimal):
        n = _d(n)
        if n is None:
            return False

    (sign, d, e) = n.normalize().as_tuple()
    return e >= 0
is_int.__doc__ = ('is_int(n), determine whether n is an integer.')

def ln(x):
    if float(x) > 0:
        return math.log(float(x))
    else:
        raise ValueError(_('Logarithm(x) only defined for x > 0'))
ln.__doc__ = _(
'ln(x), return the natural logarithm of x. This is the value for which the \
exponent exp() equals x. Defined for x >= 0.')

def log10(x):
    if float(x) > 0:
        return math.log(float(x))
    else:
        raise ValueError(_('Logarithm(x) only defined for x > 0'))
log10.__doc__ = _(
'log10(x), return the base 10 logarithm of x. This is the value y for which \
10^y equals x. Defined for x >= 0.')

def mod(x, y):
    if is_int(y):
        return x % y
    else:
        raise ValueError(_('Can only calculate x modulo <integer>'))
mod.__doc__ = _(
'mod(x, y), return the modulus of x with respect to y. This is the remainder \
after dividing x by y.')

def mul(x, y):
    if isinstance(x, _Decimal) or isinstance(y, _Decimal):
        x = _d(x)
        y = _d(y)
    return x * y
mul.__doc__ = _('mul(x, y), return x * y')

def negate(x):
    return -x
negate.__doc__ = _('negate(x), return -x')

def Or(x, y):
    return x | y
Or.__doc__ = _(
'Or(x, y), logical or. Returns True if x or y is True, else returns False')

def pow(x, y):
    if is_int(y):
        if is_int(x):
            return long(x) ** int(y)
        elif hasattr(x, '__pow__'):
            return x ** y
        else:
            return float(x) ** int(y)
    else:
        if isinstance(x, _Decimal) or isinstance(y, _Decimal):
            x = _d(x)
            y = _d(y)
        return _d(math.pow(float(x), float(y)))
pow.__doc__ = _('pow(x, y), return x to the power y (x**y)')

def rand_float():
    return random.random()
rand_float.__doc__ = _(
'rand_float(), return a random floating point number between 0.0 and 1.0')

def rand_int(maxval=65535):
    return random.randint(0, maxval)
rand_int.__doc__ = _(
'rand_int([<maxval>]), return a random integer between 0 and <maxval>. \
<maxval> is an optional argument and is set to 65535 by default.')

def round(x):
    return math.round(float(x))
round.__doc__ = _('round(x), return the integer nearest to x.')

def shift_left(x, y):
    if is_int(x) and is_int(y):
        return _d(int(x) << int(y))
    else:
        raise ValueError(_('Bitwise operations only apply to integers'))
shift_left.__doc__ = _(
'shift_left(x, y), shift x by y bits to the left (multiply by 2 per bit)')

def shift_right(x, y):
    if is_int(x) and is_int(y):
        return _d(int(x) >> int(y))
    else:
        raise ValueError(_('Bitwise operations only apply to integers'))
shift_right.__doc__ = _(
'shift_right(x, y), shift x by y bits to the right (divide by 2 per bit)')

def sin(x):
    return math.sin(_scale_angle(x))
sin.__doc__ = _(
'sin(x), return the sine of x. This is the y-coordinate on the unit circle at \
the angle x')

def sinh(x):
    return math.sinh(x)
sinh.__doc__ = _(
'sinh(x), return the hyperbolic sine of x. Given by (exp(x) - exp(-x)) / 2')

def sinc(x):
    if float(x) == 0.0:
        return 1
    return sin(x) / x
sinc.__doc__ = _(
'sinc(x), return the sinc of x. This is given by sin(x) / x.')

def sqrt(x):
    return math.sqrt(float(x))
sqrt.__doc__ = _(
'sqrt(x), return the square root of x. This is the value for which the square \
equals x. Defined for x >= 0.')

def square(x):
    return x**2
square.__doc__ = _('square(x), return x * x')

def sub(x, y):
    if isinstance(x, _Decimal) or isinstance(y, _Decimal):
        x = _d(x)
        y = _d(y)
    return x - y
sub.__doc__ = _('sub(x, y), return x - y')

def tan(x):
    return math.tan(_scale_angle(x))
tan.__doc__ = _(
'tan(x), return the tangent of x. This is the slope of the line from the origin \
of the unit circle to the point on the unit circle defined by the angle x. Given \
by sin(x) / cos(x)')

def tanh(x):
    return math.tanh(x)
tanh.__doc__ = _(
'tanh(x), return the hyperbolic tangent of x. Given by sinh(x) / cosh(x)')

def xor(x, y):
    return x ^ y
xor.__doc__ = _(
'xor(x, y), logical xor. Returns True if either x is True (and y is False) \
or y is True (and x is False), else returns False')

