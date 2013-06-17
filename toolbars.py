# -*- coding: utf-8 -*-
# toolbars.py, see CalcActivity.py for info

import pygtk
pygtk.require('2.0')
import gtk
from mathlib import MathLib

from sugar.graphics.palette import Palette
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toggletoolbutton import ToggleToolButton
from sugar.graphics.style import GRID_CELL_SIZE

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
        if 'icon' in items[0] and _icon_exists(items[0]['icon']):
            self.set_named_icon(items[0]['icon'])
        elif 'html' in items[0]:
            self.set_label(items[0]['html'])
#        self.set_tooltip(items[0][1])
        self.set_tooltip(desc)
        self.selected = 0
        self.connect('clicked', self.toggle_button)
        self.callback = cb

    def toggle_button(self, w):
        self.selected = (self.selected + 1) % len(self.items)
        but = self.items[self.selected]
        if 'icon' in but and _icon_exists(but['icon']):
            self.set_named_icon(but['icon'])
        elif 'html' in but:
            _logger.info('Setting html: %s', but['html'])
            self.set_label(but['html'])
#        self.set_tooltip(but[1])
        if self.callback is not None:
            if 'html' in but:
                self.callback(but['html'])
            else:
                self.callback(but)

class TextToggleToolButton(gtk.ToggleToolButton):
    def __init__(self, items, cb, desc, index=False):
        gtk.ToggleToolButton.__init__(self)
        self.items = items
        self.set_label(items[0])
        self.selected = 0
        self.connect('clicked', self.toggle_button)
        self.callback = cb
        self.index = index
        self.set_tooltip_text(desc)

    def toggle_button(self, w):
        self.selected = (self.selected + 1) % len(self.items)
        but = self.items[self.selected]
        self.set_label(but)
        if self.callback is not None:
            if self.index:
                self.callback(self.selected)
            else:
                self.callback(but)

class LineSeparator(gtk.SeparatorToolItem):
    def __init__(self):
        gtk.SeparatorToolItem.__init__(self)
        self.set_draw(True)

class EditToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        copy_tool = ToolButton('edit-copy')
        copy_tool.set_tooltip(_('Copy'))
        copy_tool.set_accelerator(_('<ctrl>c'))
        copy_tool.connect('clicked', lambda x: calc.text_copy())
        self.insert(copy_tool, -1)

        menu_item = MenuItem(_('Cut'))

        try:
            menu_item.set_accelerator(_('<ctrl>x'))
        except AttributeError:
            pass

        menu_item.connect('activate', lambda x: calc.text_cut())
        menu_item.show()
        copy_tool.get_palette().menu.append(menu_item)

        self.insert(IconToolButton('edit-paste', _('Paste'),
            lambda x: calc.text_paste(),
            alt_html='Paste'), -1)
                        
        self.show_all()

class AlgebraToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('algebra-square', _('Square'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '**2'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(square)'),
            alt_html='x<sup>2</sup>'), -1)

        self.insert(IconToolButton('algebra-sqrt', _('Square root'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sqrt'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(sqrt)'),
            alt_html='√x'), -1)

        self.insert(IconToolButton('algebra-xinv', _('Inverse'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '**-1'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(inv)'),
            alt_html='x<sup>-1</sup>'), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('algebra-exp', _('e to the power x'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'exp'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(exp)'),
            alt_html='e<sup>x</sup>'), -1)

        self.insert(IconToolButton('algebra-xpowy', _('x to the power y'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'pow'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(pow)'),
            alt_html='x<sup>y</sup>'), -1)

        self.insert(IconToolButton('algebra-ln', _('Natural logarithm'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'ln'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(ln)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('algebra-fac', _('Factorial'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'fac'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(fac)')), -1)
            
        self.show_all()

class TrigonometryToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('trigonometry-sin', _('Sine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sin'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(sin)')), -1)

        self.insert(IconToolButton('trigonometry-cos', _('Cosine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'cos'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(cos)')), -1)

        self.insert(IconToolButton('trigonometry-tan', _('Tangent'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'tan'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(tan)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('trigonometry-asin', _('Arc sine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'asin'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(asin)')), -1)

        self.insert(IconToolButton('trigonometry-acos', _('Arc cosine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'acos'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(acos)')), -1)

        self.insert(IconToolButton('trigonometry-atan', _('Arc tangent'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'atan'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(atan)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('trigonometry-sinh', _('Hyperbolic sine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'sinh'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(sinh)')), -1)

        self.insert(IconToolButton('trigonometry-cosh', _('Hyperbolic cosine'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'cosh'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(cosh)')), -1)

        self.insert(IconToolButton('trigonometry-tanh', _('Hyperbolic tangent'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'tanh'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(tanh)')), -1)
            
        self.show_all()

class BooleanToolbar(gtk.Toolbar):
    def __init__(self, calc):
        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('boolean-and', _('Logical and'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '&'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(And)')), -1)

        self.insert(IconToolButton('boolean-or', _('Logical or'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '|'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(Or)')), -1)

#        self.insert(IconToolButton('boolean-xor', _('Logical xor'),
#            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '^'),
#            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(xor)')), -1)

        self.insert(LineSeparator(), -1)

        self.insert(IconToolButton('boolean-eq', _('Equals'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '==')), -1)

        self.insert(IconToolButton('boolean-neq', _('Not equals'),
            lambda x: calc.button_pressed(calc.TYPE_OP_POST, '!=')), -1)
            
        self.show_all()

class MiscToolbar(gtk.Toolbar):
    def __init__(self, calc, target_toolbar=None):
        self._target_toolbar = target_toolbar

        gtk.Toolbar.__init__(self)

        self.insert(IconToolButton('constants-pi', _('Pi'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'pi'),
            alt_html='π'), -1)

        self.insert(IconToolButton('constants-e', _('e'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'e')), -1)

        self.insert(IconToolButton('constants-eulersconstant', _('γ'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, '0.577215664901533')), -1)

        self.insert(IconToolButton('constants-goldenratio', _('φ'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, '1.618033988749895')), -1)

        self._line_separator1 = LineSeparator()
        self._line_separator2 = LineSeparator()

        self._plot_button = IconToolButton('plot', _('Plot'),
            lambda x: calc.button_pressed(calc.TYPE_FUNCTION, 'plot'),
            lambda x: calc.button_pressed(calc.TYPE_TEXT, 'help(plot)'))

        el = [
            {'icon': 'format-deg', 'desc': _('Degrees'), 'html': 'deg'},
            {'icon': 'format-rad', 'desc': _('Radians'), 'html': 'rad'},
        ]
        self._angle_button = IconToggleToolButton(
            el, 
            lambda x: self.update_angle_type(x, calc),
            _('Degrees / Radians'))
        self.update_angle_type('deg', calc)

        el = [
            {'icon': 'format-sci', 'html': 'sci'},
            {'icon': 'format-exp', 'html': 'exp'},
        ]
        self._format_button = IconToggleToolButton(
            el,
            lambda x: self.update_format_type(x, calc),
            _('Exponent / Scientific notation'))

        el = [
            {'icon': 'digits-9', 'html': '9'},
            {'icon': 'digits-12', 'html': '12'},
            {'icon': 'digits-15', 'html': '15'},
            {'icon': 'digits-6', 'html': '6'},
        ]
        self._digits_button = IconToggleToolButton(
                el,
                lambda x: self.update_digits(x, calc),
                _('Number of shown digits'))

        el = [
            {'icon': 'base-10', 'html': '10'},
            {'icon': 'base-2', 'html': '2'},
            {'icon': 'base-16', 'html': '16'},
            {'icon': 'base-8', 'html': '8'}
        ]
         
        self._base_button = IconToggleToolButton(
            el,
            lambda x: self.update_int_base(x, calc),
            _('Integer formatting base'))

        self.update_layout()

        self.show_all()

    def update_layout(self):
        if gtk.gdk.screen_width() < 14 * GRID_CELL_SIZE or \
                self._target_toolbar is None:
            target_toolbar = self
            if self._target_toolbar is not None:
                self._remove_buttons(self._target_toolbar)
        else:
            target_toolbar = self._target_toolbar
            self._remove_buttons(self)

        target_toolbar.insert(self._line_separator1, -1)

        target_toolbar.insert(self._plot_button, -1)

        target_toolbar.insert(self._line_separator2, -1)

        target_toolbar.insert(self._angle_button, -1)
        target_toolbar.insert(self._format_button, -1)
        target_toolbar.insert(self._digits_button, -1)
        target_toolbar.insert(self._base_button, -1)

    def _remove_buttons(self, toolbar):
        for item in [self._plot_button, self._line_separator1,
                     self._line_separator2, self._angle_button,
                     self._format_button, self._digits_button,
                     self._base_button]:
            toolbar.remove(item)

    def update_angle_type(self, text, calc):
        var = calc.parser.get_var('angle_scaling')
        if var is None:
            _logger.warning('Variable angle_scaling not defined.')
            return

        if text == 'deg':
            var.value = MathLib.ANGLE_DEG
        elif text == 'rad':
            var.value = MathLib.ANGLE_RAD
        _logger.debug('Angle scaling: %s', var.value)

    def update_format_type(self, text, calc):
        if text == 'exp':
            calc.ml.set_format_type(MathLib.FORMAT_EXPONENT)
        elif text == 'sci':
            calc.ml.set_format_type(MathLib.FORMAT_SCIENTIFIC)
        _logger.debug('Format type: %s', calc.ml.format_type)

    def update_digits(self, text, calc):
        calc.ml.set_digit_limit(int(text))
        _logger.debug('Digit limit: %s', calc.ml.digit_limit)

    def update_int_base(self, text, calc):
        calc.ml.set_integer_base(int(text))
        _logger.debug('Integer base: %s', calc.ml.integer_base)

