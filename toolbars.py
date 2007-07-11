import pygtk
pygtk.require('2.0')
import gtk

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
    def __init__(self, text, cb):
        gtk.ToggleToolButton.__init__(self)
        self.set_label(text)
        self.selected = False
        self.connect('clicked', cb)

class IconToggleToolButton(ToggleToolButton):
    def __init__(self, text, cb):
        ToggleToolButton.__init__(self, text)
        self.connect('clicked', cb)

class LineSeparator(gtk.SeparatorToolItem):
    def __init__(self):
        gtk.SeparatorToolItem.__init__(self)
        self.set_draw(True)

class EditToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

class AlgebraToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(TextToolButton('square',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '^2')), -1)

        self.insert(TextToolButton('sqrt',
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sqrt')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(TextToolButton('exp',
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, 'exp')), -1)

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
        self.insert(TextToggleToolButton('rad/deg',
           lambda b: FormatToolbar.toggle_button(b)), -1)
    
    @staticmethod
    def toggle_button(button):
        _logger.debug("Toggle button with button:%s",button)
        button.selected = not button.selected
        if button.selected:
            button.set_label('rad/DEG')
        else:
            button.set_label('RAD/deg')
