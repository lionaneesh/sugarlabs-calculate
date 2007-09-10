# toolbars.py, see CalcActivity.py for info

import pygtk
pygtk.require('2.0')
import gtk
from mathlib import MathLib
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toggletoolbutton import ToggleToolButton

import logging
_logger = logging.getLogger('calc-activity')

class TextToolButton(gtk.ToolButton):
    def __init__(self, text, cb):
        gtk.ToolButton.__init__(self)
        self.set_label(text)
        self.connect('clicked', cb)

class IconToolButton(ToolButton):
    def __init__(self, text, cb):
        ToolButton.__init__(self, text)
        self.connect('clicked', cb)

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
        self.set_label(self.items[self.selected])
        if self.callback is not None:
            self.callback(self.items[self.selected])

class IconToggleToolButton(ToggleToolButton):
    def __init__(self, text, cb):
        ToggleToolButton.__init__(self, text)
        self.connect('clicked', self.toggle_button)

    def toggle_button(self, w):
        if self.callback is not None:
            self.callback(self.items[self.selected])

class LineSeparator(gtk.SeparatorToolItem):
    def __init__(self):
        gtk.SeparatorToolItem.__init__(self)
        self.set_draw(True)

class EditToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(TextToolButton('Copy',
            lambda x: calc.text_copy()), -1)

        self.insert(TextToolButton('Paste',
            lambda x: calc.text_paste()), -1)

        self.insert(TextToolButton('Cut',
            lambda x: calc.text_cut()), -1)

class AlgebraToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(TextToolButton('square',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '^2')), -1)

        self.insert(TextToolButton('sqrt',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sqrt')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(TextToolButton('exp',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'exp')), -1)

        self.insert(TextToolButton('ln',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'ln')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(TextToolButton('fac',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '!')), -1)

class TrigonometryToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(TextToolButton('sin',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sin')), -1)

        self.insert(TextToolButton('cos',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'cos')), -1)

        self.insert(TextToolButton('tan',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'tan')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(TextToolButton('asin',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'asin')), -1)

        self.insert(TextToolButton('acos',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'acos')), -1)

        self.insert(TextToolButton('atan',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'atan')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(TextToolButton('sinh',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sinh')), -1)

        self.insert(TextToolButton('cosh',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'cosh')), -1)

        self.insert(TextToolButton('tanh',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'tanh')), -1)

class BooleanToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(TextToolButton('and',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '&')), -1)

        self.insert(TextToolButton('or',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '|')), -1)

        self.insert(TextToolButton('xor',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '^')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(TextToolButton('eq',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '=')), -1)

        self.insert(TextToolButton('neq',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '!=')), -1)

class ConstantsToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(TextToolButton('pi',
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'pi')), -1)

        self.insert(TextToolButton('e',
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'e')), -1)

class FormatToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)
        el = ['deg', 'rad']
        self.insert(TextToggleToolButton(el, 
                    lambda x: self.update_angle_type(x, calc)), -1)
    
    def update_angle_type(self, text, calc):
        if text == 'deg':
            calc.ml.set_angle_type(MathLib.ANGLE_DEG)
        elif text == 'rad':
            calc.ml.set_angle_type(MathLib.ANGLE_RAD)
        _logger.debug('Angle type: %s', self.ml.angle_scaling)
