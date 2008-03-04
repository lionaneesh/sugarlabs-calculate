# -*- coding: UTF-8 -*-
# toolbars.py, see CalcActivity.py for info

import pygtk
pygtk.require('2.0')
import gtk
from mathlib import MathLib

from sugar.graphics.palette import Palette
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toggletoolbutton import ToggleToolButton

import logging
_logger = logging.getLogger('calc-activity')

from gettext import gettext as _

def _icon_exists(name):
    if name == '':
        return False

    theme = gtk.icon_theme_get_default()
    info = theme.lookup_icon(name, 0, 0)
    if info:
        return True

    return False

class IconToolButton(ToolButton):
    def __init__(self, icon_name, text, cb, help_cb=None, alt_html=''):
        ToolButton.__init__(self)

        if _icon_exists(icon_name):
            self.set_icon(icon_name)
        else:
            if alt_html == '':
                alt_html = icon_name

            label = gtk.Label()
            label.set_markup(alt_html)
            label.show()
            self.set_label_widget(label)

        self.create_palette(text, help_cb)

        self.connect('clicked', cb)

    def create_palette(self, text, help_cb):
        p = Palette(text)

        if help_cb is not None:
            item = MenuItem(_('Help'), 'action-help')
            item.connect('activate', help_cb)
            item.show()
            p.menu.append(item)

        self.set_palette(p)

class IconToggleToolButton(ToggleToolButton):

    def __init__(self, items, cb, desc):
        ToggleToolButton.__init__(self)
        self.items = items
        if _icon_exists(items[0][0]):
            self.set_named_icon(items[0][0])
        else:
            self.set_label(items[0][0])
#        self.set_tooltip(items[0][1])
        self.set_tooltip(desc)
        self.selected = 0
        self.connect('clicked', self.toggle_button)
        self.callback = cb

    def toggle_button(self, w):
        self.selected = (self.selected + 1) % len(self.items)
        but = self.items[self.selected]
        if _icon_exists(but[0]):
            self.set_named_icon(but[0])
        else:
            self.set_label(but[0])
#        self.set_tooltip(but[1])
        if self.callback is not None:
            self.callback(but[0])

class TextToggleToolButton(gtk.ToggleToolButton):
    def __init__(self, items, cb):
        gtk.ToggleToolButton.__init__(self)
        self.items = items
        self.set_label(items[0])
        self.selected = 0
        self.connect('clicked', self.toggle_button)
        self.callback = cb

    def toggle_button(self, w):
        self.selected = (self.selected + 1) % len(self.items)
        but = self.items[self.selected]
        self.set_label(but)
        if self.callback is not None:
            self.callback(but)

class LineSeparator(gtk.SeparatorToolItem):
    def __init__(self):
        gtk.SeparatorToolItem.__init__(self)
        self.set_draw(True)

class EditToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('edit-copy', _('Copy'),
            lambda x: calc.text_copy(),
            alt_html='Copy'), -1)

        self.insert(IconToolButton('edit-paste', _('Paste'),
            lambda x: calc.text_paste(),
            alt_html='Paste'), -1)

        self.insert(IconToolButton('edit-cut', _('Cut'),
            lambda x: calc.text_cut(),
            alt_html='Cut'), -1)

class AlgebraToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('square', _('Square'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '^2'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(square)'),
            alt_html='x<sup>2</sup>'), -1)

        self.insert(IconToolButton('sqrt', _('Square root'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sqrt'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(sqrt)'),
            alt_html='√x'), -1)

        self.insert(IconToolButton('xinv', _('Inverse'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '^-1'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(inv)'),
            alt_html='x<sup>-1</sup>'), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('exp', _('e to the power x'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'exp'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(exp)'),
            alt_html='e<sup>x</sup>'), -1)

        self.insert(IconToolButton('xpowy', _('x to the power y'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'pow'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(pow)'),
            alt_html='x<sup>y</sup>'), -1)

        self.insert(IconToolButton('ln', _('Natural logarithm'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'ln'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(ln)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('fac', _('Factorial'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '!'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(fac)')), -1)

class TrigonometryToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('sin', _('Sine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sin'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(sin)')), -1)

        self.insert(IconToolButton('cos', _('Cosine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'cos'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(cos)')), -1)

        self.insert(IconToolButton('tan', _('Tangent'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'tan'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(tan)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('asin', _('Arc sine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'asin'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(asin)')), -1)

        self.insert(IconToolButton('acos', _('Arc cosine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'acos'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(acos)')), -1)

        self.insert(IconToolButton('atan', _('Arc tangent'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'atan'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(atan)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('sinh', _('Hyperbolic sine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sinh'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(sinh)')), -1)

        self.insert(IconToolButton('cosh', _('Hyperbolic cosine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'cosh'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(cosh)')), -1)

        self.insert(IconToolButton('tanh', _('Hyperbolic tangent'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'tanh'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(tanh)')), -1)

class BooleanToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('and', _('Logical and'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '&'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(and))')), -1)

        self.insert(IconToolButton('or', _('Logical or'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '|'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(or)')), -1)

#        self.insert(IconToolButton('xor', _('Logical xor'),
#            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '^'),
#            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(xor)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('eq', _('Equals'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '=')), -1)

        self.insert(IconToolButton('neq', _('Not equals'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '!=')), -1)

class ConstantsToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('pi', _('Pi'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'pi'),
            alt_html='π'), -1)

        self.insert(IconToolButton('e', _('e'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'e')), -1)

class FormatToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)
        el = [
            ['deg', _('Degrees')],
            ['rad', _('Radians')]
        ]
        self.insert(IconToggleToolButton(el, 
                    lambda x: self.update_angle_type(x, calc),
                    _('Degrees / radians')), -1)
    
    def update_angle_type(self, text, calc):
        if text == 'deg':
            calc.ml.set_angle_type(MathLib.ANGLE_DEG)
        elif text == 'rad':
            calc.ml.set_angle_type(MathLib.ANGLE_RAD)
        _logger.debug('Angle type: %s', self.ml.angle_scaling)
