# -*- coding: UTF-8 -*-

import types
import parser
import re
import inspect
import math
import logging

from gettext import gettext as _

# Python 2.6 has a 'public' ast module
try:
    import ast
except ImportError:
    import _ast as ast

from mathlib import MathLib
from plotlib import PlotLib

PLOTHELP = _(
"plot(eqn, var=-a..b), plot the equation 'eqn' with the variable 'var' in the \
range from a to b")

class ParseError(Exception):
    def __init__(self, msg, start, end=None):
        self._msg = msg

        if end is None:
            end = start + 1
        self._range = (start, end)

    def get_range(self):
        return self._range

    def __str__(self):
        msg = _("Error at %d") % (self._range[0] + 1)
        if self._msg is not None and len(self._msg) > 0:
            msg += ": %s" % (self._msg)
        return msg

class Helper:

    def __init__(self, parent):
        self._parent = parent
        self._topics = {}
        self.add_help('test',
            _('This is just a test topic, use help(index) for the index'))

    def add_help(self, topic, text):
        self._topics[unicode(topic)] = _(text)
        self._topics[unicode(_(topic))] = _(text)

    def get_help(self, topic=None):
        if isinstance(topic, ast.Name):
            topic = topic.id
        elif isinstance(topic, ast.Str):
            topic = topic.s
        elif type(topic) not in (types.StringType, types.UnicodeType) or len(topic) == 0:
            return _("Use help(test) for help about 'test', or help(index) for the index")

        # TRANS: This command is descriptive, so can be translated
        if topic in ('index', _('index'), 'topics', _('topics')):
            ret = _('Topics') + ': '
            topics = self._topics.keys()
            topics.append('index')
            topics.sort()
            ret += ', '.join(topics)
            return ret

        # TRANS: This command is descriptive, so can be translated
        if topic in ('variables', _('variables')):
            ret = _('Variables') + ': '
            variables = self._parent.get_variable_names()
            ret += ', '.join(variables)
            return ret

        # TRANS: This command is descriptive, so can be translated
        if topic in ('functions', _('functions')):
            ret = _('Functions') + ': '
            functions = self._parent.get_function_names()
            ret += ', '.join(functions)
            return ret

        for (key, val) in self._topics.iteritems():
            if topic == key or _(topic) == key:
                return val

        return _("No help about '%s' available, use help(index) for the index") % (topic)

class AstParser:
    '''
    Equation parser based on python's ast (abstract syntax tree) module.
    In 2.5 this is a private module, but in 2.6 it is public.
    '''

    OPERATOR_MAP = {
        u'⨯': '*',
        u'×': '*',
        u'÷': '/',
        '^': '**',
    }

    DIADIC_OPS = (
        '+', '-', '*', u'⨯', u'×', u'÷' , '/', '^', '**',
        '&', '|', '=', '!=', '<', '>', '<<', '>>', '%',
    )

    PRE_OPS = (
        '-', '+', '~',
    )

    POST_OPS = (
    )

    FLOAT_REGEXP_STR = '([+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?)'
    FLOAT_REGEXP = re.compile(FLOAT_REGEXP_STR)
    RANGE_REGEXP = re.compile(FLOAT_REGEXP_STR + '\.\.' + FLOAT_REGEXP_STR)

    # Unary and binary operator maps.
    # Mappings to a string will be replaced by calls to MathLib functions
    # with the same name.

    UNARYOP_MAP = {
        ast.UAdd: lambda x: x,
        ast.USub: lambda x: -x,
        ast.Not: lambda x: not x,
    }

    BINOP_MAP = {
        ast.Add: 'add',
        ast.And: lambda x, y: x and y,
        ast.BitAnd: lambda x, y: x & y,
        ast.BitOr: lambda x, y: x | y,
        ast.BitXor: lambda x, y: x ^ y,
        ast.Div: 'div',
        ast.FloorDiv: 'div',
        ast.LShift: 'shift_left',
        ast.Mod: 'mod',
        ast.Mult: 'mul',
        ast.NotEq: lambda x, y: x != y,
        ast.Or: lambda x, y: x or y,
        ast.Pow: 'pow',
        ast.RShift: 'shift_right',
        ast.Sub: 'sub',
    }
    
    CMPOP_MAP = {
        ast.Gt: lambda x, y: x > y,
        ast.GtE: lambda x, y: x >= y,
        ast.Is: lambda x, y: x == y,
        ast.IsNot: lambda x, y: x != y,
        ast.Lt: lambda x, y: x < y,
        ast.LtE: lambda x, y: x <= y,
    }

    _ARG_STRING = 0
    _ARG_NODE = 1

    def __init__(self, ml=None, pl=None):
        self._namespace = {}

        if ml is None:
            self.ml = MathLib()
        else:
            self.ml = ml

        if pl is None:
            self.pl = PlotLib(self)
        else:
            self.pl = pl

        # Help manager
        self._helper = Helper(self)
        self.set_var('help', self._helper.get_help)
        self._special_func_args = {
            (self._helper.get_help, 0): self._ARG_STRING,
            (self.pl.plot, 0): self._ARG_NODE,
        }

        # Plug-in plot function
        self.set_var('plot', self.pl.plot)
        self._helper.add_help('plot', PLOTHELP)

        self._load_plugins()

        # Redirect operations to registered functions
        for key, val in self.UNARYOP_MAP.iteritems():
            if type(val) is types.StringType:
                self.UNARYOP_MAP[key] = self.get_var(val)
        for key, val in self.BINOP_MAP.iteritems():
            if type(val) is types.StringType:
                self.BINOP_MAP[key] = self.get_var(val)

    def _load_plugin_items(self, items):
        for name, item in items:
            if name.startswith('_') or type(item) is types.ModuleType:
                continue

            self.set_var(name, item)
            if type(item) in (types.FunctionType, types.ClassType):
                if item.__doc__ is not None:
                    self._helper.add_help(name, item.__doc__)

    def _load_plugins(self):
        plugins = ('functions', 'constants')
        for plugin in plugins:
            try:
                exec('import %s' % plugin)
                exec('_mod = %s' % plugin)
                items = inspect.getmembers(_mod)
                self._load_plugin_items(items)

            except Exception, e:
                logging.error('Error loading plugin: %s', e)

    def log_debug_info(self):
        logging.debug('Variables:')
        for name in self.get_variable_names():
            logging.debug('    %s', name)
        logging.debug('Functions:')
        for name in self.get_function_names():
            logging.debug('    %s', name)
        logging.debug('Unary ops:')
        for op in self.UNARYOP_MAP.keys():
            logging.debug('    %s', op)
        logging.debug('Binary ops:')
        for op in self.BINOP_MAP.keys():
            logging.debug('    %s', op)

    def set_var(self, name, value):
        '''Set variable <name> to <value>, which could be a function too.'''
        self._namespace[unicode(name)] = value

    def get_var(self, name):
        '''Return variable value, or None if non-existent.'''
        return self._namespace.get(unicode(name), None)

    def _get_names(self, start='', include_vars=True):
        ret = []
        for key, val in self._namespace.iteritems():
            if type(val) is types.ClassType:
                for key2, val2 in inspect.getmembers(val):
                    if key2.startswith('_'):
                        continue

                    b = type(val2) not in (types.FunctionType, types.MethodType)
                    if not include_vars:
                        b = not b
                    if b and key2.startswith(start):
                            ret.append(key2)

            else:
                b = type(val) not in (types.FunctionType, types.MethodType)
                if not include_vars:
                    b = not b
                if b and key.startswith(start):
                    ret.append(key)

        ret.sort()
        return ret

    def get_names(self, start=''):
        '''Return a list with names of all defined variables/functions.'''
        ret = []
        for key, val in self._namespace.iteritems():
            if key.startswith(start):
                ret.append(key)

        return ret

    def get_variable_names(self, start=''):
        '''Return a list with names of all defined variables.'''
        return self._get_names(start, include_vars=True)

    def get_function_names(self, start=''):
        '''Return a list with names of all defined function.'''
        return self._get_names(start, include_vars=False)

    def add_help(self, topic, text):
        self._help_topics[topic] = text

    def get_diadic_operators(self):
        return self.DIADIC_OPS

    def get_post_operators(self):
        return self.POST_OPS

    def get_pre_operators(self):
        return self.PRE_OPS

    def _resolve_arg(self, func, index, arg, level):
        funcarg = (func, index)
        if funcarg in self._special_func_args:
            val = self._special_func_args[funcarg]
            if val == self._ARG_NODE:
                return arg
            if val == self._ARG_STRING:
                if isinstance(arg, ast.Name):
                    return arg.id
                elif isinstance(arg, ast.Str):
                    return arg.s
                else:
                    logging.error('Unable to resolve special arg %r', arg)
        else:
            return self._process_node(arg, level)

    def _process_node(self, node, level=0, isfunc=False):
        ofs = node.col_offset

        if node is None:
            return None

        elif isinstance(node, ast.Expression):
            return self._process_node(node.body)

        elif isinstance(node, ast.BinOp):
            left = self._process_node(node.left, level + 1)
            right = self._process_node(node.right, level + 1)
            if left is None or right is None:
                return None
            func = self.BINOP_MAP[type(node.op)]
            return func(left, right)

        elif isinstance(node, ast.UnaryOp):
            operand = self._process_node(node.operand, level + 1)
            if operand is None:
                return None
            func = self.UNARYOP_MAP[type(node.op)]
            return func(operand)

        elif isinstance(node, ast.Compare):
            left = self._process_node(node.left)
            right = self._process_node(node.comparators[0])
            func = self.CMPOP_MAP[type(node.ops[0])]
            return func(left, right)

        elif isinstance(node, ast.Call):
            func = self._process_node(node.func, level + 1, isfunc=True)
            if func is None:
                return None

            for i in range(len(node.args)):
                node.args[i] = self._resolve_arg(func, i, node.args[i], level + 1)
                if node.args[i] is None:
                    return None
            kwargs = {}
            for i in range(len(node.keywords)):
                key = node.keywords[i].arg
                val = self._process_node(node.keywords[i].value, level + 1)
                if key is None or val is None:
                    return None
                kwargs[key] = val

            try:
                ret = func(*node.args, **kwargs)
                return ret
            except Exception, e:
                msg = str(e)
                raise ParseError(msg, ofs)

        elif isinstance(node, ast.Num):
            return node.n

        elif isinstance(node, ast.Str):
            return node.s

        elif isinstance(node, ast.Tuple):
            list = [self._process_node(i, level + 1) for i in node.elts]
            return tuple(list)

        elif isinstance(node, ast.Name):
            if not isfunc and node.id in ('help', _('help')):
                return self._helper.get_help()

            elif node.id in self._namespace:
                var = self.get_var(node.id)
                if type(var) is ast.Expression:
                    return self._process_node(var.body)
                else:
                    return var
            else:
                if isfunc:
                    msg = _("Function '%s' not defined") % (node.id)
                else:
                    msg = _("Variable '%s' not defined") % (node.id)
                    raise ParseError(msg, ofs, ofs + len(node.id))

        elif isinstance(node, ast.Attribute):
            parent = self._process_node(node.value)
            if parent:
                try:
                    val = parent.__dict__[node.attr]
                    return val
                except Exception, e:
                    msg = _("Attribute '%s' does not exist)") % node.value
                    raise ParseError(msg, ofs, ofs + len(node.value))

            return None

        else:
            logging.debug('Unknown node: %r', repr(node))

        return None

    def _preprocess_eqn(self, eqn):
        eqn = unicode(eqn)
        for key, val in self.OPERATOR_MAP.iteritems():
            eqn = eqn.replace(key, val)

        # Replace a..b ranges with (a,b)
        eqn = self.RANGE_REGEXP.sub(r'(\1,\3)', eqn)

        return eqn

    def parse(self, eqn):
        '''
        Parse an equation and return a parse tree.
        '''

        eqn = self._preprocess_eqn(eqn)
        logging.debug('Parsing preprocessed equation: %r', eqn)

        try:
            tree = compile(eqn, '<string>', 'eval', ast.PyCF_ONLY_AST)
        except SyntaxError, e:
            msg = _('Parse error')
            raise ParseError(msg, e.offset - 1)

        return tree

    def evaluate(self, eqn):
        '''
        Evaluate an equation or parse tree.
        '''

        if type(eqn) in (types.StringType, types.UnicodeType):
            eqn = self.parse(eqn)

        if isinstance(eqn, ast.Expression):
            ret = self._process_node(eqn.body)
        else:
            ret = self._process_node(eqn)

        if type(ret) is types.FunctionType:
            return ret()
        else:
            return ret

    def parse_and_eval(self, eqn):
        '''
        Parse and evaluate an equation.
        '''

        tree = self.parse(eqn)
        if tree is not None:
            return self.evaluate(tree)
        else:
            return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    p = AstParser()
    eqn = 'sin(45)'
    ret = p.evaluate(eqn)
    print 'Eqn: %s, ret: %s' % (eqn, ret)

    eqn = '2<=physics.c'
    ret = p.evaluate(eqn)
    print 'Eqn: %s, ret: %s' % (eqn, ret)

    eqn = 'help(functions)'
    ret = p.evaluate(eqn)
    print 'Eqn: %s, ret: %s' % (eqn, ret)

    eqn = 'factorize(105)'
    ret = p.evaluate(eqn)
    print 'Eqn: %s, ret: %s' % (eqn, ret)

    eqn = 'plot(x**2,x=-2..2)'
    ret = p.evaluate(eqn)
    print 'Eqn: %s, ret: %s' % (eqn, ret)

    p.set_var('a', 123)
    eqn = 'a * 5'
    ret = p.evaluate(eqn)
    print 'Eqn: %s, ret: %s' % (eqn, ret)

