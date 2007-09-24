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

class Callable:
    def __init__(self, f):
        self.__call__ = f

# Just an example implementation; should be fixed for internationalization
class EqnParserHelp():

    DICT = {
    "acos": "help_acos",
    "asin": "help_asin",
    "exp": "help_exp",
    "functions": "help_functions",
    "operators": "help_operators",
    "plot": "help_plot",
    "sqrt": "help_sqrt",
    "test": "help_test",
    "variables": "help_variables",
    }

    def __init__(self):
        return

    def help(about):
        if type(about) != types.StringType or len(about) == 0:
            return _("help_usage")

        if about == "index":
            ret = _("Topics") + ": "
            for (key, val) in EqnParserHelp.DICT.iteritems():
                ret += key + " "
            return ret

        ret = ""
        for (key, val) in EqnParserHelp.DICT.iteritems():
            if about.find(key) != -1:
                ret += _(val)

        if ret == "":
            ret += _("No help about '%s' available, use help(index) for the index") % (about)

        return ret

    help = Callable(help)
