# eqnparserhelp.py, help functions for the equation parser by
# Reinier Heeres <reinier@heeres.eu>
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
#    2007-09-16: rwh, first version

import types
from gettext import gettext as _

import logging
_logger = logging.getLogger('EqnParser')

class Callable:
    def __init__(self, f):
        self.__call__ = f

class EqnParserHelp():

    # Unfortunately gettext is not yet initialized at the time _() is called here.
    # Still do it like this to make sure these strings show up in the POT-file
    DICT = {
        # TRANS: It is possible to translate commands. However, I would highly
        # recommend NOT doing so for mathematical functions like cos(). help(),
        # functions() etc should be translated.
        _("acos"): _(
"acos(x), return the arc cosine of x. This is the angle for which the cosine \
is x. Defined for -1 <= x < 1"),

        _("and"): _(
"and(x, y), logical and. Returns True if x and y are True, else returns False"),

        _("asin"): _(
"asin(x), return the arc sine of x. This is the angle for which the sine is x. \
Defined for -1 <= x <= 1"),

        _("atan"): _(
"atan(x), return the arc tangent of x. This is the angle for which the tangent \
is x. Defined for all x"),

        _("cos"): _(
"cos(x), return the cosine of x. This is the x-coordinate on the unit circle \
at the angle x"),

        _("cosh"): _(
"cosh(x), return the hyperbolic cosine of x. Given by (exp(x) + exp(-x)) / 2"),

        _("exp"): _(
"exp(x), return the natural exponent of x. Given by e^x"),

        _("fac"): _(
"fac(x), return the factorial of x. Given by x * (x - 1) * (x - 2) * ..."),

        # TRANS: This command is descriptive, so can be translated
        _("functions"): _(
"functions(), return a list of all the functions that are defined"),

        _("ln"): _(
"ln(x), return the natural logarithm of x. This is the value for which the \
exponent exp() equals x. Defined for x >= 0."),

        # TRANS: This command is descriptive, so can be translated
        _("operators"): _(
"operators(), return a list of the operators that are defined"),

        _("or"): _(
"or(x, y), logical or. Returns True if x and/or y are True, else return False"),

        _("plot"): _(
"plot(eqn, var=-a..b), plot the equation 'eqn' with the variable 'var' in the \
range from a to b"),

        _("sin"): _(
"sin(x), return the sine of x. This is the y-coordinate on the unit circle at \
the angle x"),

        _("sinh"): _(
"sinh(x), return the hyperbolic sine of x. Given by (exp(x) - exp(-x)) / 2"),

        _("sqrt"): _(
"sqrt(x), return the square root of x. This is the value for which the square \
equals x. Defined for x >= 0."),

        _("square"): _(
"square(x), return the square of x. Given by x * x"
        ),

        _("tan"): _(
"tan(x), return the tangent of x. This is the slope of the line from the origin \
of the unit circle to the point on the unit circle defined by the angle x. Given \
by sin(x) / cos(x)"),

        _("tanh"): _(
"sinh(x), return the hyperbolic tangent of x. Given by sinh(x) / cosh(x)"),

        _("test"): _(
"This is just a test topic, use help(index) for the index"),

        # TRANS: This command is descriptive, so can be translated
        _("variables"): _(
"variables(), return a list of the variables that are currently defined"),

        _("xor"): _(
"xor(x, y), logical xor. Returns True if either x is True (and y is False) \
or y is True (and x is False), else returns False"),

    }

    def __init__(self):
        pass

    def help(about):
        t = type(about)
        if (t != types.StringType and t != types.UnicodeType) or len(about) == 0:
            return _("Use help(test) for help about 'test', or help(index) for the index")

        # TRANS: help(index), both 'index' and the translation  will work
        if about == "index" or about == _("index"):
            ret = _("Topics") + ": "
            for (key, val) in EqnParserHelp.DICT.iteritems():
                ret += key + " "
            return ret

        ret = ""
        for (key, val) in EqnParserHelp.DICT.iteritems():
            if about == key:
                ret += val

        if ret == "":
           ret += _("No help about '%s' available, use help(index) for the index") % (about)

        return ret

    help = Callable(help)
