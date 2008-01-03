# -*- coding: UTF-8 -*-
# eqnparser.py, generic equation parser by Reinier Heeres <reinier@heeres.eu>
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

import logging
_logger = logging.getLogger('EqnParser')

import types
from mathlib import MathLib
from plotlib import PlotLib
from eqnparserhelp import EqnParserHelp

from rational import Rational

from gettext import gettext as _

_generic_error = _('Parse error')

class Equation:
    def __init__(self, eqn):
        self.equation = eqn

class ParserState:
    OK = 1
    PARSE_ERROR = 2

    def __init__(self, str):
        self.str = str
        self.strlen = len(str)
        if self.strlen > 0:
            self.char = str[0]
        else:
            self.char = None
        self.ofs = 0
        self.level = -1
        self.result_type = EqnParser.TYPE_UNKNOWN
        self.error_code = self.OK
        self.error_msg = ""
        self.error_range = (0, 0)

    def state_string(self):
        return _('level: %d, ofs %d') % (self.level, self.ofs)

    def more(self):
        return self.error_code == self.OK and self.ofs < self.strlen

    def next(self):
        self.ofs += 1
        if self.ofs < self.strlen:
            self.char = self.str[self.ofs]
        else:
            self.char = None
        return self.char

    def prev(self):
        self.ofs -= 1
        if self.ofs < self.strlen and self.ofs >= 0:
            self.char = self.str[self.ofs]
        else:
            self.char = None
        return self.char

    def set_ofs(self, o):
        self.ofs = o
        self.char = self.str[o]

    def inc_level(self):
        self.level += 1

    def dec_level(self):
        self.level -= 1

    def set_type(self, t):
        if self.result_type == EqnParser.TYPE_UNKNOWN or t is EqnParser.TYPE_SYMBOLIC:
            self.result_type = t
            return True
        elif self.result_type != t:
            _logger.debug('Type error')
            return False
        else:
            return True

    def set_error(self, c, msg=None, range=None):
        self.error_code = c
        if msg is not None:
            self.error_msg = msg
        if range is not None:
            _logger.debug('Setting range: %r', range)
            self.error_range = range
        else:
            _logger.debug('Setting offset: %d', self.ofs)
            self.error_range = (self.ofs, self.ofs + 1)

    def get_error(self):
        return self.error_code

    def set_error_range(self, r):
        self.error_range = r

    def format_error(self):
        msg = _("Error at %d") % (self.error_range[0])
        if self.error_msg is not None and len(self.error_msg) > 0:
            msg += ": %s" % (self.error_msg)
        return msg

    def copy_error(self, ps):
        """Copy error state from recursively created ParserState object"""
        self.error_code = ps.error_code
        self.error_msg = ps.error_msg
        self.error_range = (ps.error_range[0] + ps.ofs, ps.error_range[1] + ps.ofs)

class EqnParser:
    OP_INVALID = -1
    OP_PRE = 1
    OP_POST = 2
    OP_DIADIC = 3
    OP_ASSIGN = 4

    INVALID_OP = ('err', OP_INVALID, 0, lambda x: False)

    NAME_CHARS = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789 '
    DIGITS = u'0123456789'
    SPACE_CHARS = u'\t \r\n'

# These will be filled from register_operator
    OP_START_CHARS = u""
    OP_CHARS = u""

    TYPE_UNKNOWN = 1
    TYPE_INT = 2
    TYPE_FLOAT = 3
    TYPE_BOOL = 4
    TYPE_SYMBOLIC = 5

    def __init__(self, ml=None):
        if ml is None:
            self.ml = MathLib()
        else:
            self.ml = ml

        self.ps = None

        self.pl = PlotLib(self)

        self.variables = {}
        self.parse_var = {}     # Whether or not to parse this variable recursively
        self.functions = {}
        self.operators = []

        self.cached_diadic_ops = None
        self.cached_pre_ops = None
        self.cached_post_ops = None

        self.register_function('exp', lambda x: self.ml.exp(x[0]), {"nargs": 1})
        self.register_function('ln', lambda x: self.ml.ln(x[0]), {"nargs": 1})
        self.register_function('log', lambda x: self.ml.log10(x[0]), {"nargs": 1})
        self.register_function('log10', lambda x: self.ml.log10(x[0]), {"nargs": 1})
        self.register_function('pow', lambda x: self.ml.pow(x[0], x[1]), {"nargs": 2})

        self.register_function('sqrt', lambda x: self.ml.sqrt(x[0]), {"nargs": 1})

        self.register_function('sin', lambda x: self.ml.sin(x[0]), {"nargs": 1})
        self.register_function('cos', lambda x: self.ml.cos(x[0]), {"nargs": 1})
        self.register_function('tan', lambda x: self.ml.tan(x[0]), {"nargs": 1})

        self.register_function('asin', lambda x: self.ml.asin(x[0]), {"nargs": 1})
        self.register_function('acos', lambda x: self.ml.acos(x[0]), {"nargs": 1})
        self.register_function('atan', lambda x: self.ml.atan(x[0]), {"nargs": 1})

        self.register_function('sinh', lambda x: self.ml.sinh(x[0]), {"nargs": 1})
        self.register_function('cosh', lambda x: self.ml.cosh(x[0]), {"nargs": 1})
        self.register_function('tanh', lambda x: self.ml.tanh(x[0]), {"nargs": 1})

        self.register_function('asinh', lambda x: self.ml.asinh(x[0]), {"nargs": 1})
        self.register_function('acosh', lambda x: self.ml.acosh(x[0]), {"nargs": 1})
        self.register_function('atanh', lambda x: self.ml.atanh(x[0]), {"nargs": 1})

        self.register_function('round', lambda x: self.ml.round(x[0]), {"nargs": 1})
        self.register_function('floor', lambda x: self.ml.floor(x[0]), {"nargs": 1})
        self.register_function('ceil', lambda x: self.ml.ceil(x[0]), {"nargs": 1})

        self.register_function('rand', lambda x: self.ml.rand_float(), {"nargs": 0})
        self.register_function('randint', lambda x: self.ml.rand_int(), {"nargs": 0})

        self.register_function('mod', lambda x: self.ml.mod(x[0], x[1]), {"nargs": 2})

        self.register_function('factorize', lambda x: self.ml.factorize(x[0]), {"nargs": 1})

        self.register_function('plot', lambda x: self.pl.plot(x[0], x[1]), {"nargs": 2, 'parse_options': False})

        self.register_function('help', lambda x: EqnParserHelp.help(x[0]), {"nargs": 1, 'parse_options': False})

        self.register_function('functions', lambda x: self.functions_string(), {"nargs": 0})
        self.register_function('variables', lambda x: self.variables_string(), {"nargs": 0})
        self.register_function('operators', lambda x: self.operators_string(), {"nargs": 0})

        self.register_operator('+', self.OP_DIADIC, 0, lambda x: self.ml.add(x[0], x[1]))
        self.register_operator('+', self.OP_PRE, 2, lambda x: x[0])
        self.register_operator('-', self.OP_DIADIC, 0, lambda x: self.ml.sub(x[0], x[1]))
        self.register_operator('-', self.OP_PRE, 2, lambda x: self.ml.negate(x[0]))
        self.register_operator('*', self.OP_DIADIC, 1, lambda x: self.ml.mul(x[0], x[1]))
        self.register_operator(u'⨯', self.OP_DIADIC, 1, lambda x: self.ml.mul(x[0], x[1]))
        self.register_operator(u'×', self.OP_DIADIC, 1, lambda x: self.ml.mul(x[0], x[1]))
        self.register_operator('/', self.OP_DIADIC, 1, lambda x: self.div_operator(x[0], x[1]))
        self.register_operator(u'÷', self.OP_DIADIC, 1, lambda x: self.div_operator(x[0], x[1]))

        self.register_operator('^', self.OP_DIADIC, 2, lambda x: self.ml.pow(x[0], x[1]))
        self.register_operator('**', self.OP_DIADIC, 2, lambda x: self.ml.pow(x[0], x[1]))

        self.register_operator('!', self.OP_POST, 0, lambda x: self.ml.factorial(x[0]))

        self.register_operator('&', self.OP_DIADIC, 0, lambda x: x[0] and x[1])
        self.register_function('and', lambda x: x[0] and x[1], {"nargs": 2})
        self.register_operator('|', self.OP_DIADIC, 0, lambda x: x[0] or x[1])
        self.register_function('or', lambda x: x[0] or x[1], {"nargs": 2})
        self.register_operator('!', self.OP_PRE, 0, lambda x: not x[0])
        self.register_function('not', lambda x: not x[0], {"nargs": 1})

#        self.register_operator('^', self.OP_PRE, 0, lambda x: not x[0])
        self.register_function('xor', lambda x: (x[0] and not x[1]) or (x[1] and not x[0]), {"nargs": 2})

        self.register_operator('=', self.OP_DIADIC, 0, lambda x: x[0] == x[1])
        self.register_operator('!=', self.OP_DIADIC, 0, lambda x: x[0] != x[1])
        self.register_operator('<', self.OP_DIADIC, 0, lambda x: x[0] < x[1])
        self.register_operator('>', self.OP_DIADIC, 0, lambda x: x[0] > x[1])

        self.register_operator('<<', self.OP_DIADIC, 0, lambda x: self.ml.shift_left(x[0], x[1]))
        self.register_operator('>>', self.OP_DIADIC, 0, lambda x: self.ml.shift_right(x[0], x[1]))

        self.register_operator('%', self.OP_DIADIC, 2, lambda x: self.ml.mod(x[0], x[1]))

        self.set_var('help',
            _("Use help(test) for help about 'test', or help(index) for the index"),
            parse=False)

    def register_function(self, name, f, opts):
        self.functions[name] = (f, opts)
        self.functions[_(name)] = (f, opts)

    def register_operator(self, op, type, presedence, f):
        self.operators.append((op, type, presedence, f))

        if op[0] not in self.OP_START_CHARS:
            self.OP_START_CHARS += op[0]
        for c in op:
            if c not in self.OP_CHARS:
                self.OP_CHARS += c

    def get_diadic_operators(self):
        if self.cached_diadic_ops == None:
            self.cached_diadic_ops = []
            for (op, type, presedence, f) in self.operators:
                if type == self.OP_DIADIC:
                    self.cached_diadic_ops.append(op)
        return self.cached_diadic_ops

    def get_pre_operators(self):
        if self.cached_pre_ops == None:
            self.cached_pre_ops = []
            for (op, type, presedence, f) in self.operators:
                if type == self.OP_PRE:
                    self.cached_pre_ops.append(op)
        return self.cached_pre_ops

    def get_post_operators(self):
        if self.cached_post_ops == None:
            self.cached_post_ops = []
            for (op, type, presedence, f) in self.operators:
                if type == self.OP_POST:
                    self.cached_post_ops.append(op)
        return self.cached_post_ops

    def reset_variable_level(self, level):
        return
#        for i in self.variables.keys():
#            self.variables[i].highest_level = level

    def set_var(self, name, val, parse=True):
        if type(val) is types.FloatType:
            self.variables[name] = self.ml.d(val)
        else:
            self.variables[name] = val
            self.parse_var[name] = parse

    def get_var(self, name):
        if name in self.variables:
            return self.variables[name]
        else:
            return None

    def lookup_var(self, name, ps):
        c = self.ml.get_constant(name)
        if c is not None:
            return c

        if name in self.variables.keys():
#            if self.variables[name].highest_level > 0 and self.variables[name].highest_level != ps.level:
#                _logger.error('EqnParser.lookup_var(): recursion detected')
#                return None
#            self.variables[name].highest_level = level
            if (type(self.variables[name]) is types.UnicodeType or type(self.variables[name]) is types.StringType) \
                and self.parse_var[name]:
                return self.parse(self.variables[name], reset=False)
            else:
                return self.variables[name]
        else:
            _logger.debug('variable %s not defined', name)
            ps.set_type(self.TYPE_SYMBOLIC)
            return None

    def get_vars(self):
        list = []
        for name in self.variables:
            list.append((name, self.variables[name]))
        return list

    def get_var_names(self, start=None):
        names = self.variables.keys()
        names.sort()

        if start is None:
            return names

        retnames = []
        for name in names:
            if name[:len(start)] == start:
                retnames.append(name)
        return retnames

    def get_function_names(self):
        names = self.functions.keys()
        names.sort()
        return names

    def eval_func(self, func, args, level):
        if func not in self.functions:
            _logger.error(_("Function '%s' not defined"), func)
            self.ps.set_error(ParserState.PARSE_ERROR, msg=_("Function '%s' not defined") % (func))
            return None

        (f, opts) = self.functions[func]
        if len(args) != opts['nargs']:
            _logger.error(_('Invalid number of arguments (%d instead of %d)'), len(args), opts['nargs'])
            self.ps.set_error(ParserState.PARSE_ERROR, msg=_('function takes %d args') % (opts['nargs']))
            return None

        if 'parse_options' in opts and opts['parse_options'] == False:
            pargs = args
        else:
            pargs = []
            for i in range(len(args)):
                pargs.append(self.parse(args[i], reset=False))
                if pargs[i] is None:
                    _logger.error(_('Unable to parse argument %d: \'%s\''), i, args[i])
                    self.ps.set_error(ParserState.PARSE_ERROR, msg=_('Unable to parse argument %d: \'%s\'') % (i, args[i]))
                    return None

        try:
            res = f(pargs)

# Maybe we should map exceptions to more obvious error messages
        except Exception, inst:
            res = None
            self.ps.set_error(ParserState.PARSE_ERROR, msg=_("Function error: %s") % (str(inst)))

        _logger.debug('Function \'%s\' returned %s', func, self.ml.format_number(res))
        return res

    def parse_number(self, ps):
        startofs = ps.ofs

# integer part
        while ps.more() and ps.char in self.DIGITS:
            ps.next()

# part after dot
        if ps.char == '.' or ps.char == self.ml.fraction_sep:
            ps.next()
            while ps.more() and ps.char in self.DIGITS:
                ps.next()

# exponent
        if ps.char is not None and ps.char in u'eE':
            ps.next()
            if ps.char is not None and ps.char in u'+-':
                ps.next()
            while ps.more() and ps.char in self.DIGITS:
                ps.next()

        _logger.debug('parse_number(): %d - %d: %s', startofs, ps.ofs, ps.str[startofs:ps.ofs])
        n = self.ml.parse_number(ps.str[startofs:ps.ofs])
        return n

    def valid_operator(self, opstr, left_val):
        for op_tuple in self.operators:
            (op, type, presedence, f) = op_tuple
            if op == opstr:
                if type == self.OP_DIADIC and left_val is not None:
                    return op_tuple
                elif type == self.OP_POST and left_val is not None:
                    return op_tuple
                elif type == self.OP_PRE and left_val is None:
                    return op_tuple
        return None

    def parse_operator(self, ps, left_val):
        startofs = ps.ofs
        op = None
        while ps.more() and ps.char in self.OP_CHARS:
            ps.next()
            op2 = self.valid_operator(ps.str[startofs:ps.ofs], left_val)
            if op2 is not None:
                op = op2
            elif op is not None:
                ps.prev()
                break

        if op is not None:
            _logger.debug('parse_operator(): %d - %d: %s', startofs, ps.ofs, ps.str[startofs:ps.ofs])
            return op
        else:
            return self.INVALID_OP

    def parse_func_args(self, ps):
        startofs = ps.ofs
        args = []
        pcount = 1
        while ps.more() and pcount > 0:
            if ps.char == ',' and pcount == 1:
                args.append(ps.str[startofs:ps.ofs])
                startofs = ps.ofs + 1
            elif ps.char == '(':
                pcount += 1
            elif ps.char == ')':
                pcount -= 1
                if pcount == 0 and (ps.ofs - startofs) > 0:
                    args.append(ps.str[startofs:ps.ofs])
            ps.next()
        _logger.debug('parse_func_args(): %d - %d: %r', startofs, ps.ofs, args)
        return args

    def parse_var_func(self, ps):
        startofs = ps.ofs
        while ps.more() and ps.char in self.NAME_CHARS:
            ps.next()
        name = ps.str[startofs:ps.ofs]
        name.strip(self.SPACE_CHARS)
        name.rstrip(self.SPACE_CHARS)

# handle function
        if ps.char == '(':
            ps.next()
            _logger.debug('parse_var_func(): function %d - %d: %s', startofs, ps.ofs, name)
            args = self.parse_func_args(ps)
            ret = self.eval_func(name, args, ps.level)
            if ret is None:
                ps.set_error_range((startofs, ps.ofs))
            return ret

# handle var
        else:
            _logger.debug('parse_var_func(): variable %d - %d: %s', startofs, ps.ofs, name)
            res = self.lookup_var(name, ps)
            if res is None:
                ps.set_error(ParserState.PARSE_ERROR, msg=_("Variable '%s' not defined") % (name), range=(startofs, ps.ofs))
            return res

    def _parse(self, ps, presedence=None):
        if presedence is None:
            ps.inc_level()
        _logger.debug('_parse(): %s, presedence: %r', ps.state_string(), presedence)

        op = None
        left_val = None
        right_val = None

        while ps.more():
#            _logger.debug('Looking at %r, ofs %d in %r', ps.char, ps.ofs, ps.str)

# Skip spaces
            if ps.char in self.SPACE_CHARS:
                ps.next()

# Left parenthesis: parse sub-expression
            elif ps.char == '(':
                if not (left_val is None or left_val is not None and op is not None):
                    _logger.error('Parse error (left parenthesis)')
                    ps.set_error(ParserState.PARSE_ERROR, msg=_("Left parenthesis unexpected"))
                    return None

                ps.next()
                left_val = self._parse(ps)

# Right parenthesis: return from parsing sub-expression
# -If we are looking ahead because of operator presedence return value
# -Else move to next character, decrease level and return value
            elif ps.char == ')':
                if presedence is not None:
                    if left_val is None:
                        _logger.error(_('Parse error (right parenthesis)'))
                        ps.set_error(ParserState.PARSE_ERROR, msg=_("Right parenthesis unexpected"))
                        return None
                    else:
                        _logger.debug('returning %s', self.ml.format_number(left_val))
                        return left_val

                if ps.level > 0:
                    ps.next()
                    ps.dec_level()
                    if left_val is None:
                        _logger.error(_('Parse error (right parenthesis, no left_val)'))
                        ps.set_error(ParserState.PARSE_ERROR, msg=_("Right parenthesis unexpected"))
                        return None
                    else:
                        _logger.debug('returning %s', self.ml.format_number(left_val))
                        return left_val
                else:
                    _logger.error(_('Parse error (right parenthesis, no level to close)'))
                    ps.set_error(ParserState.PARSE_ERROR, msg=_("Right parenthesis unexpected"))
                    return None

# Parse number
            elif ps.char == '.' or ps.char in self.DIGITS:
                if right_val is not None or left_val is not None:
                    _logger.error(_('Number not expected'))
                    ps.set_error(ParserState.PARSE_ERROR, msg=_("Number not expected"))
                    return None

                left_val = self.parse_number(ps)

# Parse operator
            elif ps.char in self.OP_START_CHARS:
                if op is not None:
                    ps.set_error(ParserState.PARSE_ERROR, msg=_("Operator not expected"))
                    return None

                startofs = ps.ofs
                op = self.parse_operator(ps, left_val)
                (opstr, otype, opres, of) = op

# Diadic operators
                if otype == self.OP_DIADIC:
                    if presedence is not None and opres <= presedence:
                        ps.set_ofs(startofs)
                        _logger.debug('returning %s (by presedence, %d)', self.ml.format_number(left_val), ps.ofs)
                        return left_val
                    else:
                        right_val = self._parse(ps, presedence=opres)
                        if right_val is None and self.ps.get_error() == ParserState.OK:
                            _logger.error(_('Parse error: number or variable expected'))
                            ps.set_error(ParserState.PARSE_ERROR, msg=_("Number or variable expected"))
                            return None
                        elif right_val is None:
                            return None

                        res = of([left_val, right_val])
                        _logger.debug('OP: %s (%r), %s (%r) ==> %s (%r)', self.ml.format_number(left_val), left_val, self.ml.format_number(right_val), right_val, self.ml.format_number(res), res)
                        left_val = res
                        right_val = None
                    op = None

# Operator that goes after value
                elif otype == self.OP_POST:
                    res = of([left_val])
                    _logger.debug('OP POST: %s ==> %s', self.ml.format_number(left_val), self.ml.format_number(res))
                    left_val = res
                    op = None

# Operator that goes before value
                elif otype == self.OP_PRE:
                    right_val = self._parse(ps, presedence=opres)
                    if right_val is None:
                        return None
                    left_val = of([right_val])
                    _logger.debug('OP PRE: %s ==> %s', self.ml.format_number(right_val), self.ml.format_number(left_val))
                    op = None

                elif otype == self.OP_INVALID:
                    _logger.debug('Invalid operator')
                    ps.set_error(ParserState.PARSE_ERROR, msg=_("Invalid operator"), range=(startofs, ps.ofs))
                    return None

# Parse variable or function
            else:
                if left_val is not None:
                    _logger.debug('Operator expected: %r', self.OP_START_CHARS)
                    ps.set_error(ParserState.PARSE_ERROR, msg=_("Operator expected"))
                    return None

                left_val = self.parse_var_func(ps)

        if not ps.more() and ps.level > 0:
            _logger.debug('Parse error: \')\' expected')
            ps.set_error(ParserState.PARSE_ERROR, msg=_("Right parenthesis unexpected"))
            return None
        elif op is None and left_val is not None:
            _logger.debug('returning %s', self.ml.format_number(left_val))
            return left_val
        else:
            _logger.error(_('_parse(): returning None'))
# Should be set somewhere already
#            ps.set_error(ParserState.PARSE_ERROR)
            return None

    def get_error_offset(self):
        return self.ps.error_range[0]

    def get_error_range(self):
        return self.ps.error_range

    def parse(self, eqn, reset=True):
        """Construct ParserState object and call _parse"""

        # Parse everything in unicode
        if type(eqn) is types.StringType:
            eqn = unicode(eqn)

        _logger.debug('parse(): %r', eqn)
        self.reset_variable_level(0)

        if reset:
            self.ps = None

        oldps = self.ps
        self.ps = ParserState(eqn)
        ret = self._parse(self.ps)
        if oldps is not None:
            oldps.copy_error(self.ps)
            self.ps = oldps

        return ret

    def functions_string(self):
        ret = ""
        for key in self.functions.keys():
            ret += key + " "
        return ret

    def variables_string(self):
        ret = ""
        for key in self.variables.keys():
            ret += key + " "
        return ret

    def operators_string(self):
        ret = ""
        for (op, type, p, f) in self.operators:
            ret += op + " "
        return ret

    def div_operator(self, a, b):
        if isinstance(a, Rational) or isinstance(b, Rational):
            return a / b
        elif self.ml.is_int(a) and self.ml.is_int(b):
            return Rational(a, b)
        else:
            return self.ml.div(a, b)
