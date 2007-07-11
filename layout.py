from gettext import gettext as _
import pygtk
pygtk.require('2.0')
import gtk
import pango

from sugar.activity import activity

from toolbars import *

class CalcLayout:

    def __init__(self, parent):
        self._parent = parent
        self.create_dialog()

    def create_color(self, rf, gf, bf):
        return gtk.gdk.Color(int(rf*0xFFFF), int(gf*0xFFFF), int(bf*0xFFFF))

    def create_button_data(self):
        self.button_data = [
# [x, y, width, label, bgcol, cb]
            [1, 1, 1, '7', self.col_gray2, lambda w: self._parent.add_text('7')],
            [2, 1, 1, '8', self.col_gray2, lambda w: self._parent.add_text('8')],
            [3, 1, 1, '9', self.col_gray2, lambda w: self._parent.add_text('9')],
      
            [1, 2, 1, '4', self.col_gray2, lambda w: self._parent.add_text('4')],
            [2, 2, 1, '5', self.col_gray2, lambda w: self._parent.add_text('5')],
            [3, 2, 1, '6', self.col_gray2, lambda w: self._parent.add_text('6')],
      
            [1, 3, 1, '1', self.col_gray2, lambda w: self._parent.add_text('1')],
            [2, 3, 1, '2', self.col_gray2, lambda w: self._parent.add_text('2')],
            [3, 3, 1, '3', self.col_gray2, lambda w: self._parent.add_text('3')],
      
            [1, 4, 1, '0', self.col_gray2, lambda w: self._parent.add_text('0')],
            [2, 4, 1, '.', self.col_gray2, lambda w: self._parent.add_text('.')],
            [3, 4, 1, 'Ans', self.col_gray2, lambda w: self._parent.add_text('Ans')],
     
            [4, 1, 3, 'clear', self.col_gray1, lambda w: self._parent.clear()],
 
            [4, 2, 1, '+', self.col_gray3, lambda w: self._parent.add_character('+')],
            [5, 2, 1, '-', self.col_gray3, lambda w: self._parent.add_character('-')],
            [6, 2, 1, '(', self.col_gray3, lambda w: self._parent.add_character('(')],
            [4, 3, 1, 'x', self.col_gray3, lambda w: self._parent.add_character('*')],
            [5, 3, 1, '/', self.col_gray3, lambda w: self._parent.add_character('/')],
            [6, 3, 1, ')', self.col_gray3, lambda w: self._parent.add_character(')')],

            [4, 4, 3, 'enter', self.col_gray1, lambda w: self._parent.process()],
        ]

    def create_dialog(self):
# Toolbar
        toolbox = activity.ActivityToolbox(self._parent)
        self._parent.set_toolbox(toolbox)
        toolbox.add_toolbar(_('Edit'), EditToolbar(self._parent))
        toolbox.add_toolbar(_('Algebra'), AlgebraToolbar(self._parent))
        toolbox.add_toolbar(_('Trigonometry'), TrigonometryToolbar(self._parent))
        toolbox.add_toolbar(_('Boolean'), BooleanToolbar(self._parent))
        toolbox.add_toolbar(_('Constants'), ConstantsToolbar(self._parent))
        toolbox.add_toolbar(_('Format'), FormatToolbar(self._parent))
        toolbox.show_all()

# Some layout constants
        self.font = pango.FontDescription(str='sans bold 15')
        self.col_white = self.create_color(1.00, 1.00, 1.00)
        self.col_gray1 = self.create_color(0.69, 0.71, 0.72)
        self.col_gray2 = self.create_color(0.51, 0.51, 0.53)
        self.col_gray3 = self.create_color(0.30, 0.30, 0.31)
        self.col_black = self.create_color(0.00, 0.00, 0.00)

# Container
        hc1 = gtk.HBox(False, 10)
        hc1.set_border_width(10)
        if issubclass(type(self._parent), gtk.Bin) and self._parent.get_child() is not None:
            self._parent.get_child().add(hc1)
        else:
            self._parent.add(hc1)

# Left part: container and input
        vc1 = gtk.VBox(False, 10)
        hc1.add(vc1)
        hc2 = gtk.HBox(False, 10)
        vc1.add(hc2)
        label1 = gtk.Label(_('Label:'))
        hc2.add(label1)
        self.label_entry = gtk.Entry()
        hc2.add(self.label_entry)
        self.text_entry = gtk.Entry()
        vc1.add(self.text_entry)
        self.text_entry.set_size_request(400, 100)
        self.text_entry.connect('key_press_event', self._parent.ignore_key_cb)
        self.text_entry.modify_font(self.font)

# Left part: buttons
        self.pad = gtk.Table(4, 6, True)
        vc1.add(self.pad)
        self.pad.set_row_spacings(6)
        self.pad.set_col_spacings(6)

        self.create_button_data()
        self.buttons = []
        for i in range(len(self.button_data)):
            x, y, w, cap, bgcol, cb = self.button_data[i]
            button = self.create_button(_(cap), cb, self.col_white, bgcol, w)
            self.buttons.append(button)
            self.pad.attach(button, x, x+w, y, y+1)

# Right part: container and equation button
        vc2 = gtk.VBox(10)
        hc1.add(vc2)
        eqbut = gtk.Button('All equations')
        vc2.add(eqbut)

# Right part: last equation

# Right part: history
        self.history = gtk.TextView()
        vc2.add(self.history)
        self.history.set_size_request(300, 400)
        self.history.set_editable(False)
        self.history.set_cursor_visible(False)

        self._parent.show_all()

    def create_button(self, cap, cb, fgcol, bgcol, width):
        button = gtk.Button(cap)
        self.modify_button_appearance(button, fgcol, bgcol, width)
        button.connect("clicked", cb)
        button.connect("key_press_event", self._parent.ignore_key_cb)
        return button

    def modify_button_appearance(self, button, fgcol, bgcol, width):
        width = 50 * width
        button.get_child().set_size_request(width, 50)
        button.get_child().modify_font(self.font)
        button.get_child().modify_fg(gtk.STATE_NORMAL, fgcol)
        button.modify_bg(gtk.STATE_NORMAL, bgcol)
