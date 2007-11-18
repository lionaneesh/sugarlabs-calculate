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
        # These are the help topics and should explain how things work
        "acos": _("help_acos"),
        "and": _("help_and"),
        "asin": _("help_asin"),
        "atan": _("help_atan"),
        "cos": _("help_cos"),
        "cosh": _("help_cosh"),
        "exp": _("help_exp"),
        "fac": _("help_fac"),
        "functions": _("help_functions"),
        "ln": _("help_ln"),
        "operators": _("help_operators"),
        "or": _("help_or"),
        "plot": _("help_plot"),
        "sin": _("help_sin"),
        "sinh": _("help_sinh"),
        "sqrt": _("help_sqrt"),
        "square": _("help_square"),
        "tan": _("help_tan"),
        "tanh": _("help_tanh"),
        "test": _("help_test"),
        "variables": _("help_variables"),
        "xor": _("help_xor"),
    }

    def __init__(self):
        pass

    def help(about):
        _logger.debug('help about %r', about)

        t = type(about)
        if (t != types.StringType and t != types.UnicodeType) or len(about) == 0:
            return _("help_usage")

        if about == "index":
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
