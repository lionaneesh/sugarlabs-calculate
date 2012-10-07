# layout.py, see calculate.py for info

from gettext import gettext as _
import pygtk
pygtk.require('2.0')
import gtk
import pango
from sugar.activity import activity
from sugar.graphics.roundbox import CanvasRoundBox
from toolbars import *

try:
    from sugar.graphics.toolbarbox import ToolbarButton, ToolbarBox
    from sugar.activity.widgets import ActivityToolbarButton
    from sugar.activity.widgets import StopButton
except ImportError:
    pass

class CalcLayout:

    FONT_SMALL_POINTS = 10
    FONT_SMALL = "sans %d" % FONT_SMALL_POINTS
    FONT_SMALL_NARROW = "sans italic %d" % FONT_SMALL_POINTS
    FONT_BIG_POINTS = 14
    FONT_BIG = "sans bold %d" % FONT_BIG_POINTS
    FONT_BIG_NARROW = "sans italic 14"
    FONT_BIGGER_POINTS = 18
    FONT_BIGGER = "sans bold %d" % FONT_BIGGER_POINTS

    def __init__(self, parent):
        self._parent = parent

        self._own_equations = []
        self._other_equations = []
        self._showing_history = True
        self._showing_all_history = True
        self._var_textviews = {}

        self.create_dialog()

    def create_color(self, rf, gf, bf):
        return gtk.gdk.Color(int(rf*0xFFFF), int(gf*0xFFFF), int(bf*0xFFFF))

    def create_button_data(self):
        """Create a list with button information. We need to do that here
        because we want to include the lambda functions."""

        mul_sym = self._parent.ml.mul_sym
        div_sym = self._parent.ml.div_sym
        equ_sym = self._parent.ml.equ_sym

        self.button_data = [
# [x, y, width, label, bgcol, cb]
            [0, 0, 2, 1, u'\u2190', self.col_gray3, lambda w: self._parent.move_left()],
            [2, 0, 2, 1, u'\u2192', self.col_gray3, lambda w: self._parent.move_right()],
            [4, 0, 2, 1, u'\u232B', self.col_gray3, lambda w: self._parent.remove_character(-1)],

            [0, 1, 1, 2, '7', self.col_gray2, lambda w: self._parent.add_text('7')],
            [1, 1, 1, 2, '8', self.col_gray2, lambda w: self._parent.add_text('8')],
            [2, 1, 1, 2, '9', self.col_gray2, lambda w: self._parent.add_text('9')],
      
            [0, 3, 1, 2, '4', self.col_gray2, lambda w: self._parent.add_text('4')],
            [1, 3, 1, 2, '5', self.col_gray2, lambda w: self._parent.add_text('5')],
            [2, 3, 1, 2, '6', self.col_gray2, lambda w: self._parent.add_text('6')],
      
            [0, 5, 1, 2, '1', self.col_gray2, lambda w: self._parent.add_text('1')],
            [1, 5, 1, 2, '2', self.col_gray2, lambda w: self._parent.add_text('2')],
            [2, 5, 1, 2, '3', self.col_gray2, lambda w: self._parent.add_text('3')],
      
            [0, 7, 2, 2, '0', self.col_gray2, lambda w: self._parent.add_text('0')],
            [2, 7, 1, 2, '.', self.col_gray2, lambda w: self._parent.add_text('.')],

            [3, 1, 3, 2, _('Clear'), self.col_gray1, lambda w: self._parent.clear()],
 
            [3, 3, 1, 2, '+', self.col_gray3, lambda w: self._parent.add_text('+')],
            [4, 3, 1, 2, '-', self.col_gray3, lambda w: self._parent.add_text('-')],
            [5, 3, 1, 2, '(', self.col_gray3, lambda w: self._parent.add_text('(')],
            [3, 5, 1, 2, mul_sym, self.col_gray3, lambda w: self._parent.add_text(mul_sym)],
            [4, 5, 1, 2, div_sym, self.col_gray3, lambda w: self._parent.add_text(div_sym)],
            [5, 5, 1, 2, ')', self.col_gray3, lambda w: self._parent.add_text(')')],

            [3, 7, 3, 2, equ_sym, self.col_gray1, lambda w: self._parent.process()],
        ]

    def create_dialog(self):
        """Setup most of the dialog."""

# Toolbar
        try:
            toolbar_box = ToolbarBox()

            activity_button = ActivityToolbarButton(self._parent)
            toolbar_box.toolbar.insert(activity_button, 0)
            
            def append(icon_name, label, page, position):
                toolbar_button = ToolbarButton()
                toolbar_button.props.page = page
                toolbar_button.props.icon_name = icon_name
                toolbar_button.props.label = label
                toolbar_box.toolbar.insert(toolbar_button, position)

            append('toolbar-edit',
                   _('Edit'),
                   EditToolbar(self._parent),
                   -1)
                                  
            append('toolbar-algebra',
                   _('Algebra'),
                   AlgebraToolbar(self._parent),
                   -1)
            
            append('toolbar-trigonometry',
                   _('Trigonometry'),
                   TrigonometryToolbar(self._parent),
                   -1)

            append('toolbar-boolean',
                   _('Boolean'),
                   BooleanToolbar(self._parent),
                   -1)

            append('toolbar-constants',
                   _('Miscellaneous'),
                   MiscToolbar(self._parent, target_toolbar=toolbar_box.toolbar),
                   5)
            
            separator = gtk.SeparatorToolItem()
            separator.props.draw = False
            separator.set_expand(True)
            separator.show()
            toolbar_box.toolbar.insert(separator, -1)

            stop = StopButton(self._parent)
            toolbar_box.toolbar.insert(stop, -1)

            toolbar_box.show_all()
            self._parent.set_toolbar_box(toolbar_box)

        except NameError:
            # Use old toolbar design
            toolbox = activity.ActivityToolbox(self._parent)
            self._parent.set_toolbox(toolbox)
            toolbox.add_toolbar(_('Edit'), EditToolbar(self._parent))
            toolbox.add_toolbar(_('Algebra'), AlgebraToolbar(self._parent))
            toolbox.add_toolbar(_('Trigonometry'), TrigonometryToolbar(self._parent))
            toolbox.add_toolbar(_('Boolean'), BooleanToolbar(self._parent))
            toolbox.add_toolbar(_('Miscellaneous'), MiscToolbar(self._parent))
            toolbox.show_all()

# Some layout constants
        self.input_font = pango.FontDescription(str='sans bold 12')
        self.button_font = pango.FontDescription(str='sans bold 16')
        self.col_white = self.create_color(1.00, 1.00, 1.00)
        self.col_gray1 = self.create_color(0.76, 0.76, 0.76)
        self.col_gray2 = self.create_color(0.50, 0.50, 0.50)
        self.col_gray3 = self.create_color(0.25, 0.25, 0.25)
        self.col_black = self.create_color(0.00, 0.00, 0.00)
        self.col_red = self.create_color(1.00, 0.00, 0.00)

# Big - Table, 16 rows, 10 columns, homogeneously divided
        self.grid = gtk.Table(26, 11, True)
        self.grid.set_border_width(0)
        self.grid.set_row_spacings(0)
        self.grid.set_col_spacings(4)

# Left part: container and input
        vc1 = gtk.VBox(False, 0)
        hc1 = gtk.HBox(False, 10)
        eb = gtk.EventBox()
        eb.add(hc1)
        eb.modify_bg(gtk.STATE_NORMAL, self.col_black)
        eb.set_border_width(12)
        eb2 = gtk.EventBox()
        eb2.add(eb)
        eb2.modify_bg(gtk.STATE_NORMAL, self.col_black)
        label1 = gtk.Label(_('Label:'))
        label1.modify_fg(gtk.STATE_NORMAL, self.col_white)
        label1.set_alignment(1, 0.5)
        hc1.pack_start(label1, expand=False, fill=False, padding=10)
        self.label_entry = gtk.Entry()
        self.label_entry.modify_bg(gtk.STATE_INSENSITIVE, self.col_black)
        hc1.pack_start(self.label_entry, expand=True, fill=True, padding=0)
        vc1.pack_start(eb2, expand=False)
        
        self.text_entry = gtk.Entry()
        self.text_entry.set_size_request(-1, 75)
        self.text_entry.connect('key_press_event', self._parent.ignore_key_cb)
        self.text_entry.modify_font(self.input_font)
        self.text_entry.modify_bg(gtk.STATE_INSENSITIVE, self.col_black)
        eb = gtk.EventBox()
        eb.add(self.text_entry)
        eb.modify_bg(gtk.STATE_NORMAL, self.col_black)
        eb.set_border_width(12)
        eb2 = gtk.EventBox()
        eb2.add(eb)
        eb2.modify_bg(gtk.STATE_NORMAL, self.col_black)
        vc1.pack_start(eb2, expand=True, fill=True, padding=0)
        self.grid.attach(vc1, 0, 7, 0, 6)

# Left part: buttons
        self.pad = gtk.Table(9, 6, True)
        self.pad.set_row_spacings(12)
        self.pad.set_col_spacings(12)
        self.pad.set_border_width(12)
        self.create_button_data()
        self.buttons = {}
        for x, y, w, h, cap, bgcol, cb in self.button_data:
            button = self.create_button(_(cap), cb, self.col_white, bgcol, w, h)
            self.buttons[cap] = button
            self.pad.attach(button, x, x + w, y, y + h)

        eb = gtk.EventBox()
        eb.add(self.pad)
        eb.modify_bg(gtk.STATE_NORMAL, self.col_black)
        self.grid.attach(eb, 0, 7, 6, 26)

# Right part: container and equation button
        hc2 = gtk.HBox()
        self.minebut = TextToggleToolButton(
            [_('All equations'), _('My equations')],
            self._all_equations_toggle_cb,
            _('Change view between own and all equations'),
            index=True)
        self.varbut = TextToggleToolButton(
            [_('Show history'), _('Show variables')],
            self._history_toggle_cb,
            _('Change view between history and variables'),
            index=True)
        hc2.add(self.minebut)
        hc2.add(self.varbut)
        self.grid.attach(hc2, 7, 11, 0, 2)
        
# Right part: last equation
        self.last_eq = gtk.TextView()
        self.last_eq.set_editable(False)
        self.last_eq.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.last_eq.connect('realize', self._textview_realize_cb)
        self.last_eq.set_border_width(2)
        self.last_eq.modify_bg(gtk.STATE_NORMAL, self.col_gray1)
        self.grid.attach(self.last_eq, 7, 11, 2, 5)

# Right part: history
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self.history_vbox = gtk.VBox()
        self.history_vbox.set_homogeneous(False)
        self.history_vbox.set_border_width(0)
        self.history_vbox.set_spacing(4)

        self.variable_vbox = gtk.VBox()
        self.variable_vbox.set_homogeneous(False)
        self.variable_vbox.set_border_width(0)
        self.variable_vbox.set_spacing(4)

        vbox = gtk.VBox()
        vbox.pack_start(self.history_vbox)
        vbox.pack_start(self.variable_vbox)
        scrolled_window.add_with_viewport(vbox)
        self.grid.attach(scrolled_window, 7, 11, 5, 26)

    def show_it(self):
        """Show the dialog."""
        self._parent.set_canvas(self.grid)
        self._parent.show_all()
        self.show_history()
        self.text_entry.grab_focus()

    def showing_history(self):
        """Return whether we're currently showing the history (or otherwise
        the list of variables)."""
        return self._showing_history

    def show_history(self):
        """Show the history VBox."""
        self._showing_history = True
        self.variable_vbox.hide()
        self.history_vbox.show()

    def add_equation(self, textview, own, prepend=False):
        """Add a gtk.TextView of an equation to the history_vbox."""

        if prepend:
            self.history_vbox.pack_start(textview, False, True)
            self.history_vbox.reorder_child(textview, 0)
        else:
            self.history_vbox.pack_end(textview, False, True)

        if own:
            self._own_equations.append(textview)
            textview.show()
        else:
            self._other_equations.append(textview)
            if self._showing_all_history:
                textview.show()

    def show_all_history(self):
        """Show both owned and other equations."""
        self._showing_all_history = True
        for key in self._other_equations:
            key.show()

    def show_own_history(self):
        """Show only owned equations."""
        self._showing_all_history = False
        for key in self._other_equations:
            key.hide()

    def add_variable(self, varname, textview):
        """Add a gtk.TextView of a variable to the variable_vbox."""

        if varname in self._var_textviews:
            self.variable_vbox.remove(self._var_textviews[varname])
            del self._var_textviews[varname]

        self._var_textviews[varname] = textview
        self.variable_vbox.pack_start(textview, False, True)

        # Reorder textviews for a sorted list
        names = self._var_textviews.keys()
        names.sort()
        for i in range(len(names)):
            self.variable_vbox.reorder_child(self._var_textviews[names[i]], i)

        textview.show()

    def show_variables(self):
        """Show the variables VBox."""
        self._showing_history = False
        self.history_vbox.hide()
        self.variable_vbox.show()

    def create_button(self, cap, cb, fgcol, bgcol, width, height):
        """Create a button that is set up properly."""
        button = gtk.Button(_(cap))
        self.modify_button_appearance(button, fgcol, bgcol, width, height)
        button.connect("clicked", cb)
        button.connect("key_press_event", self._parent.ignore_key_cb)
        return button

    def modify_button_appearance(self, button, fgcol, bgcol, width, height):
        """Modify button style."""
        width = 50 * width
        height = 50 * height
        button.get_child().set_size_request(width, height)
        button.get_child().modify_font(self.button_font)
        button.get_child().modify_fg(gtk.STATE_NORMAL, fgcol)
        button.modify_bg(gtk.STATE_NORMAL, bgcol)
        button.modify_bg(gtk.STATE_PRELIGHT, bgcol)

    def _all_equations_toggle_cb(self, index):
        if index == 0:
            self.show_all_history()
        else:
            self.show_own_history()

    def _history_toggle_cb(self, index):
        if index == 0:
            self.show_history()
        else:
            self.show_variables()

    def _textview_realize_cb(self, widget):
        '''Change textview properties once window is created.'''
        win = widget.get_window(gtk.TEXT_WINDOW_TEXT)
        win.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
        return False

