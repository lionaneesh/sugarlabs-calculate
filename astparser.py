# -*- coding: UTF-8 -*-
# astparser.py, equation parser based on python Abstract Syntax Trees (ast)
# Reinier Heeres <reinier@heeres.eu>
# Copyright (C) 2012 Aneesh Dogra <lionaneesh@gmail.com>
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

import types
import parser
import re
import inspect
import math
import copy
import logging
import decimal

from gettext import gettext as _

# Python 2.6 has a 'public' ast module
try:
    import ast
except ImportError:
    import _ast as ast

from mathlib import MathLib
from plotlib import Plot

PLOTHELP = _(
"plot(eqn, var=-a..b), plot the equation 'eqn' with the variable 'var' in the \
range from a to b")

class ParserError(Exception):
    """Parent class for exceptions raised by the parser."""

    def __init__(self, msg, start, eqn, end=None):
        self._msg = msg
        self.eqn = eqn
        self.set_range(start, end)

    def get_range(self):
        return self._range

    def set_range(self, start, end=None):
        if end is None:
            end = start + 1
        self._range = (start, end)

    def __str__(self):
        msg = _("Parse error at %d") % (self._range[0] + 1)
        if self._msg is not None and len(self._msg) > 0:
            msg += ": %s" % (self._msg)
        return msg

class ParseError(ParserError):
    """Class for error during parsing."""

    def __init__(self, msg, start, eqn, end=None):
        ParserError.__init__(self, msg, start, eqn, end)

    def __str__(self):
        msg = _("Error at '%s', position: %d") % \
              (self.eqn[self._range[0] - 1 : self._range[1] - 1],
               self._range[0])
        if self._msg is not None and len(self._msg) > 0:
            msg += ": %s" % (self._msg)
        return msg

class WrongSyntaxError(ParserError):
    """Class for reporting syntax errors."""

    def __init__(self, module=None, helper=None, start=0, end=0):
        ParserError.__init__(self,_("Syntax Error."), start, end)
        if module != None and helper != None:
            self.help_text = helper.get_help(module)
        else:
            self.help_text = None

    def __str__(self):
        msg = _("Syntax Error!")
        if self.help_text is not None and len(self.help_text) > 0:
            msg += "\n" + self.help_text
        return msg

class RuntimeError(ParserError):
    """Class for error during executing."""

    def __init__(self, msg, start, eqn, end=None):
        ParserError.__init__(self, msg, start, end)

    def __str__(self):
        msg = _("Error at '%s', position: %d") % \
              (self.eqn[self._range[0] - 1 : self._range[1] - 1],
               self._range[0])
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

class EvalState:
    '''
    Evaluation state.

    level: the current depth of recursion.
    branch_vars: the variables used in this branch.
    used_vars_ofs: dictionary of first offset where a variable is used.
    '''

    def __init__(self):
        self.level = 0
        self.branch_vars = []
        self.used_var_ofs = {}

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
    RANGE_REGEXP = re.compile('=([^,]+)\.\.([^,]+)')

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
        ast.Or: lambda x, y: x or y,
        ast.Pow: 'pow',
        ast.RShift: 'shift_right',
        ast.Sub: 'sub',
    }

    CMPOP_MAP = {
        ast.Gt: lambda x, y: x > y,
        ast.GtE: lambda x, y: x >= y,
        ast.Eq: lambda x, y: x == y,
        ast.NotEq: lambda x, y: x != y,
        ast.Lt: lambda x, y: x < y,
        ast.LtE: lambda x, y: x <= y,
    }

    _ARG_STRING = 0
    _ARG_NODE = 1

    BUILTIN_VARS = {
        'True': True,
        'False': False,
    }

    def __init__(self, ml=None, pl=None):
        self._namespace = {}
        self._immutable_vars = []
        self._used_var_ofs = {}

        if ml is None:
            self.ml = MathLib()
        else:
            self.ml = ml

        if pl is None:
            self.pl = Plot(self)
        else:
            self.pl = pl

        for key, val in self.BUILTIN_VARS.iteritems():
            self.set_var(key, val, immutable=True)

        # Help manager
        self._helper = Helper(self)
        self.set_var('help', self._helper.get_help, immutable=True)
        self._special_func_args = {
            (self._helper.get_help, 0): self._ARG_STRING,
            (self.pl.plot, 0): self._ARG_NODE,
        }

        # Plug-in plot function
        self.set_var('plot', self.pl.plot, immutable=True)
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

    def set_var(self, name, value, immutable=False):
        '''Set variable <name> to <value>, which could be a function too.'''
        name = unicode(name)
        if name in self._immutable_vars:
            return False
        self._namespace[unicode(name)] = value
        if immutable:
            self._immutable_vars.append(name)
        return True

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

    def _resolve_arg(self, func, index, arg, state):
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
            return self._process_node(arg, state)

    def _process_node(self, node, state, isfunc=False):
        # Copy state, list objects will remain the same
        state = copy.copy(state)
        state.level += 1
        ofs = getattr(node, 'col_offset', 0)

        if node is None:
            return None

        elif isinstance(node, ast.Expression):
            return self._process_node(node.body, state)

        elif isinstance(node, ast.Expr):
            return self._process_node(node.value, state)

        elif isinstance(node, ast.BinOp):
            left = self._process_node(node.left, state)
            right = self._process_node(node.right, state)
            if left is None or right is None:
                return None
            func = self.BINOP_MAP[type(node.op)]
            try:
                return func(left, right)
            except Exception, e:
                raise RuntimeError(str(e), node.right.col_offset - 1)

        elif isinstance(node, ast.UnaryOp):
            operand = self._process_node(node.operand, state)
            if operand is None:
                return None
            func = self.UNARYOP_MAP[type(node.op)]
            return func(operand)

        elif isinstance(node, ast.Compare):
            left = self._process_node(node.left, state)
            right = self._process_node(node.comparators[0], state)
            func = self.CMPOP_MAP[type(node.ops[0])]
            return func(left, right)

        elif isinstance(node, ast.Call):
            func = self._process_node(node.func, state, isfunc=True)
            if func is None:
                return None

            args = [self._resolve_arg(func, i, node.args[i], state) \
                    for i in range(len(node.args))]

            kwargs = {}
            for i in range(len(node.keywords)):
                key = node.keywords[i].arg
                val = self._process_node(node.keywords[i].value, state)
                if key is None or val is None:
                    return None
                kwargs[key] = val

            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception, e:
                msg = str(e)
                raise RuntimeError(msg, ofs)

        elif isinstance(node, ast.Num):
            if type(node.n) == types.FloatType:
                val = decimal.Decimal(str(node.n))
                return val
            return node.n

        elif isinstance(node, ast.Str):
            return node.s

        elif isinstance(node, ast.Tuple):
            list = [self._process_node(i, state) for i in node.elts]
            return tuple(list)

        elif isinstance(node, ast.Name):
            if not isfunc and node.id in ('help', _('help')):
                return self._helper.get_help()

            elif node.id in self._namespace:
                if not isfunc:
                    # Check whether variable was already used in this branch
                    if node.id in state.branch_vars:
                        raise RuntimeError(_('Recursion detected'), ofs)
                    state.branch_vars = copy.copy(state.branch_vars)

                    # Update where variable is first used
                    if node.id not in state.used_var_ofs.keys():
                        state.used_var_ofs[node.id] = node.col_offset
                    elif node.col_offset < state.used_var_ofs[node.id]:
                        state.used_var_ofs[node.id] = node.col_offset

                var = self.get_var(node.id)
                try:
                    if type(var) is ast.Expression:
                        return self._process_node(var.body, state)
                    elif type(var) is ast.Expr:
                        return self._process_node(var.value, state)
                    else:
                        return var
                except ParserError, e:
                    logging.debug('error: %r', e)
                    e.set_range(ofs, ofs + len(node.id))
                    raise e

            else:
                if isfunc:
                    msg = _("Function '%s' not defined") % (node.id)
                else:
                    msg = _("Variable '%s' not defined") % (node.id)
                raise RuntimeError(msg, ofs, ofs + len(node.id))

        elif isinstance(node, ast.Attribute):
            parent = self._process_node(node.value, state)
            if parent:
                try:
                    val = parent.__dict__[node.attr]
                    return val
                except Exception, e:
                    msg = _("Attribute '%s' does not exist") % node.value
                    raise RuntimeError(msg, ofs, ofs + len(node.value))

            return None

        else:
            logging.debug('Unknown node: %r', repr(node))

        return None

    def walk_replace_node(self, node, func, level=0):
        '''
        Walk an ast tree and call func(node) on each node. If the function
        call returns something different from None, the field will be
        replaced by the return value.

        The tree is processed depth-first. This function can be used to
        evaluate a parse tree symbolically by reducing it to unresolvable
        items only.
        '''

        if hasattr(node, '_fields') and node._fields is not None:
            for field in node._fields:
                fieldval = getattr(node, field)
                self.walk_replace_node(fieldval, func, level=level+1)
                ret = func(fieldval, level=level)
                if ret is not None:
                    setattr(node, field, ret)

    def replace_variable(self, tree, var, replacement):
        '''Replace ast.Name of name <var> with <replacement>.'''

        def func(node, **kwargs):
            if isinstance(node, ast.Name) and node.id == var:
                return replacement
            return None

        self.walk_replace_node(tree, func)

    def print_tree(self, tree):
        '''Print an ast tree.'''

        def func(node, **kwargs):
            spaces = '  ' * kwargs['level']
            print '%s%s' % (spaces, node)
            return None

        self.walk_replace_node(tree, func)

    def _parse_func(self, node, level):
        if isinstance(node, ast.BinOp):
            if isinstance(node.left, ast.Num) and isinstance(node.right, ast.Num):
                func = self.BINOP_MAP[type(node.op)]
                ans = func(node.left.n, node.right.n)
                ret = ast.Num()
                ret.n = ans
                return ret
            else:
                return None
        elif isinstance(node, ast.Name):
            if node.id in self._namespace:
                var = self.get_var(node.id)
                ret = ast.Num()
                ret.n = var
                return ret

    def parse_symbolic(self, tree):
        '''
        Reduce an abstract syntax tree until it contains only numbers and
        unresolved symbols.
        '''
        self.walk_replace_node(tree, self._parse_func)

    def _preprocess_eqn(self, eqn):
        eqn = unicode(eqn)
        for key, val in self.OPERATOR_MAP.iteritems():
            eqn = eqn.replace(key, val)

        # Replace =a..b ranges with (a,b)
        eqn = self.RANGE_REGEXP.sub(r'=(\1,\2)', eqn)

        return eqn

    def parse(self, eqn):
        '''
        Parse an equation and return a parse tree.
        '''

        eqn = self._preprocess_eqn(eqn)
        logging.debug('Parsing preprocessed equation: %r', eqn)

        try:
            tree = compile(eqn, '<string>', 'exec', ast.PyCF_ONLY_AST)
        except SyntaxError, e:
            # if we don't have an offset, its a SyntaxError
            if e.offset == None:
                if eqn.startswith('plot'):
                    raise WrongSyntaxError('plot', self._helper, len(eqn),
                                           len(eqn) + len("Syntax Error!"))
                else:
                    raise WrongSyntaxError()
            else:
                msg = _('Parse error')
                raise ParseError(msg, e.offset - 1, eqn)

        if isinstance(tree, ast.Module):
            if len(tree.body) != 1:
                msg = _("Multiple statements not supported")
                raise ParseError(msg)
            return tree.body[0]

        return tree

    def evaluate(self, eqn):
        '''
        Evaluate an equation or parse tree.
        '''

        if type(eqn) in (types.StringType, types.UnicodeType):
            eqn = self.parse(eqn)

        state = EvalState()
        try:
            if isinstance(eqn, ast.Expression):
                ret = self._process_node(eqn.body, state)
            else:
                ret = self._process_node(eqn, state)
        except (RuntimeError, ParserError), e:
            raise e
        except Exception, e:
            logging.error('Internal error (%s): %s', type(e), str(e))
            msg = _('Internal error')
            raise ParseError(msg, 0)

        self._used_var_ofs = state.used_var_ofs

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

    def get_last_used_vars(self):
        '''
        Return the variables that were accessed during the last evaluation
        of an equation tree.
        '''
        return self._used_var_ofs.keys()

    def get_var_used_ofs(self, varname):
        '''
        Return where variable <varname> is first used.
        '''
        if self._used_var_ofs is None:
            return None
        return self._used_var_ofs.get(varname, None)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    p = AstParser()

    eqn = 'a = 1'
    tree = p.parse(eqn)
    p.print_tree(tree)

    eqn = '12 * 1 + 3 * (apples - 1)'
    tree = p.parse(eqn)
    print 'Tree before:'
    p.print_tree(tree)
#    p.set_var('apples', 123)
    p.parse_symbolic(tree)
#    num = ast.Num()
#    num.n = 123
#    p.replace_variable(tree, 'apples', num)
    print 'Tree after:'
    p.print_tree(tree)

    eqns = (
        'sin(45)',
        '2<=physics.c',
        'help(functions)',
        'factorize(105)',
#        'plot(x**2,x=-2..2*(pi+1))',
        '(2 != 3) == False',
        '2343.04*.85',
        '1.23e25*.85',
    )
    for eqn in eqns:
        ret = p.evaluate(eqn)
        print 'Eqn: %s, ret: %s' % (eqn, ret)

    p.set_var('a', 123)
    eqn = 'a * 5'
    ret = p.evaluate(eqn)
    print 'Eqn: %s, ret: %s' % (eqn, ret)
