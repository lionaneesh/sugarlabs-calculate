# -*- coding: UTF-8 -*-
# calculate.py, sugar calculator, by:
#   Reinier Heeres <reinier@heeres.eu>
#   Miguel Alvarez <miguel@laptop.org>
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

import types
import os
from gettext import gettext as _
import string
import logging
_logger = logging.getLogger('Calculate')

import gobject
import pygtk
pygtk.require('2.0')
import gtk
import pango
import base64

from sugar.activity import activity
import sugar.profile
from sugar.graphics.icon import CanvasIcon
from sugar.graphics.xocolor import XoColor

from shareable_activity import ShareableActivity
from layout import CalcLayout
from mathlib import MathLib
from astparser import AstParser, ParserError, RuntimeError
from svgimage import SVGImage

from decimal import Decimal
from rational import Rational

def findchar(text, chars, ofs=0):
    '''
    Find a character in set <chars> starting from offset ofs.
    Everything between brackets '()' is ignored.
    '''

    level = 0
    for i in range(ofs, len(text)):
        if text[i] in chars and level == 0:
            return i
        elif text[i] == '(':
            level += 1
        elif text[i] == ')':
            level -= 1

    return -1

def _textview_realize_cb(widget):
    '''Change textview properties once window is created.'''
    win = widget.get_window(gtk.TEXT_WINDOW_TEXT)
    win.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
    return False

class Equation:
    def __init__(self, label=None, eqn=None, res=None, col=None, owner=None, \
            eqnstr=None, ml=None):

        if eqnstr is not None:
            self.parse(eqnstr)
        elif eqn is not None:
            self.set(label, eqn, res, col, owner)

        self.ml = ml

    def set(self, label, eqn, res, col, owner):
        """Set equation properties."""

        self.label = label
        self.equation = eqn
        self.result = res
        self.color = col
        self.owner = owner

    def __str__(self):
        if isinstance(self.result, SVGImage):
            svg_data = "<svg>" + base64.b64encode(self.result.get_svg_data())
            return "%s;%s;%s;%s;%s\n" % \
                (self.label, self.equation, svg_data, self.color.to_string(), self.owner)
        else:
            return "%s;%s;%s;%s;%s\n" % \
                (self.label, self.equation, self.result, self.color.to_string(), self.owner)

    def parse(self, str):
        """Parse equation object string representation."""

        str = str.rstrip("\r\n")
        l = str.split(';')
        if len(l) != 5:
            _logger.error(_('Equation.parse() string invalid (%s)'), str)
            return False

        if l[2].startswith("<svg>"):
            l[2] = SVGImage(data=base64.b64decode(l[2][5:]))

# Should figure out how to use MathLib directly in a non-hacky way
        else:
            try:
                l[2] = Decimal(l[2])
            except Exception, inst:
                pass

        self.set(l[0], l[1], l[2], XoColor(color_string=l[3]), l[4])

    def determine_font_size(self, *tags):
        size = 0
        for tag in tags:
            try:
                size = max(size, tag.get_property('size'))
            except:
                pass
        return size

    def append_with_superscript_tags(self, buf, text, *tags):
        '''Add a text to a gtk.TextBuffer with superscript tags.'''

        fontsize = self.determine_font_size(*tags)
        _logger.debug('font-size: %d', fontsize)
        tagsuper = buf.create_tag(rise=fontsize/2)

        ENDSET = list(AstParser.DIADIC_OPS)
        ENDSET.extend((',', '(', ')'))

        ofs = 0
        while ofs <= len(text) and text.find('**', ofs) != -1:
            nextofs = text.find('**', ofs)
            buf.insert_with_tags(buf.get_end_iter(), text[ofs:nextofs], *tags)
            nextofs2 = findchar(text, ENDSET, nextofs + 2)
            _logger.debug('nextofs2: %d, char=%c', nextofs2, text[nextofs2])
            if nextofs2 == -1:
                nextofs2 = len(text)
            buf.insert_with_tags(buf.get_end_iter(), text[nextofs+2:nextofs2],
                    tagsuper, *tags)
            ofs = nextofs2

        if ofs < len(text):
            buf.insert_with_tags(buf.get_end_iter(), text[ofs:], *tags)

    def create_lasteq_textbuf(self):
        '''
        Return a gtk.TextBuffer properly formatted for last equation
        gtk.TextView.
        '''

        is_error = isinstance(self.result, ParserError)
        buf = gtk.TextBuffer()
        tagsmallnarrow = buf.create_tag(font=CalcLayout.FONT_SMALL_NARROW)
        tagbignarrow = buf.create_tag(font=CalcLayout.FONT_BIG_NARROW)
        tagbigger = buf.create_tag(font=CalcLayout.FONT_BIGGER)
        tagjustright = buf.create_tag(justification=gtk.JUSTIFY_RIGHT)
        tagred = buf.create_tag(foreground='#FF0000')

        # Add label and equation
        if len(self.label) > 0:
            labelstr = '%s:' % self.label
            buf.insert_with_tags(buf.get_end_iter(), labelstr, tagbignarrow)
        eqnoffset = buf.get_end_iter().get_offset()
        eqnstr = '%s\n' % str(self.equation)
        if is_error:
            buf.insert_with_tags(buf.get_end_iter(), eqnstr, tagbignarrow)
        else:
            self.append_with_superscript_tags(buf, eqnstr, tagbignarrow)

        # Add result
        if type(self.result) in (types.StringType, types.UnicodeType):
            resstr = str(self.result)
            buf.insert_with_tags(buf.get_end_iter(), resstr,
                    tagsmallnarrow, tagjustright)
        elif is_error:
            resstr = str(self.result)
            buf.insert_with_tags(buf.get_end_iter(), resstr, tagsmallnarrow)
            range = self.result.get_range()
            eqnstart = buf.get_iter_at_offset(eqnoffset + range[0])
            eqnend = buf.get_iter_at_offset(eqnoffset + range[1])
            buf.apply_tag(tagred, eqnstart, eqnend)
        elif not isinstance(self.result, SVGImage):
            resstr = self.ml.format_number(self.result)
            self.append_with_superscript_tags(buf, resstr, tagbigger,
                    tagjustright)

        return buf

    def create_history_object(self):
        """
        Create a history object for this equation.
        In case of an SVG result this will be the image, otherwise it will
        return a properly formatted gtk.TextView.
        """

        if isinstance(self.result, SVGImage):
            return self.result.get_image()

        w = gtk.TextView()
        w.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.color.get_fill_color()))
        w.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.color.get_stroke_color()))
        w.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        w.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 4)
        w.set_border_window_size(gtk.TEXT_WINDOW_RIGHT, 4)
        w.set_border_window_size(gtk.TEXT_WINDOW_TOP, 4)
        w.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM, 4)
        w.connect('realize', _textview_realize_cb)
        buf = w.get_buffer()

        tagsmall = buf.create_tag(font=CalcLayout.FONT_SMALL)
        tagsmallnarrow = buf.create_tag(font=CalcLayout.FONT_SMALL_NARROW)
        tagbig = buf.create_tag(font=CalcLayout.FONT_BIG,
            justification=gtk.JUSTIFY_RIGHT)
        # TODO Fix for old Sugar 0.82 builds, red_float not available
        bright = (gtk.gdk.color_parse(self.color.get_fill_color()).red_float +
                  gtk.gdk.color_parse(self.color.get_fill_color()).green_float +
                  gtk.gdk.color_parse(self.color.get_fill_color()).blue_float) / 3.0
        if bright < 0.5:
            col = gtk.gdk.color_parse('white')
        else:
            col = gtk.gdk.color_parse('black')
        tagcolor = buf.create_tag(foreground=col)

        # Add label, equation and result
        if len(self.label) > 0:
            labelstr = '%s:' % self.label
            buf.insert_with_tags(buf.get_end_iter(), labelstr, tagsmallnarrow)
        eqnstr = '%s\n' % str(self.equation)
        self.append_with_superscript_tags(buf, eqnstr, tagsmall)

        resstr = self.ml.format_number(self.result)
        if len(resstr) > 30:
            restag = tagsmall
        else:
            restag = tagbig
        self.append_with_superscript_tags(buf, resstr, restag)

        buf.apply_tag(tagcolor, buf.get_start_iter(), buf.get_end_iter())

        return w

class Calculate(ShareableActivity):

    TYPE_FUNCTION = 1
    TYPE_OP_PRE = 2
    TYPE_OP_POST = 3
    TYPE_TEXT = 4
    

    SELECT_NONE = 0
    SELECT_SELECT = 1
    SELECT_TAB = 2

    KEYMAP = {
        'Return': lambda o: o.process(),
        'period': '.',
        'equal': '=',
        'plus': '+',
        'minus': '-',
        'asterisk': '*',
        'multiply': '×',
        'divide': '÷',
        'slash': '/',
        'BackSpace': lambda o: o.remove_character(-1),
        'Delete': lambda o: o.remove_character(1),
        'parenleft': '(',
        'parenright': ')',
        'exclam': '!',
        'ampersand': '&',
        'bar': '|',
        'asciicircum': '^',
        'less': '<',
        'greater': '>',
        'percent': '%',
        'comma': ',',
        'underscore': '_',
        'Left': lambda o: o.move_left(),
        'Right': lambda o: o.move_right(),
        'Up': lambda o: o.get_older(),
        'Down': lambda o: o.get_newer(),
        'colon': lambda o: o.label_entered(),
        'Home': lambda o: o.text_entry.set_position(0),
        'End': lambda o: o.text_entry.set_position(len(o.text_entry.get_text())),
        'Tab': lambda o: o.tab_complete(),
    }

    CTRL_KEYMAP = {
        'c': lambda o: o.text_copy(),
        'v': lambda o: o.text_paste(),
        'x': lambda o: o.text_cut(),
        'q': lambda o: o.close(),
    }

    SHIFT_KEYMAP = {
        'Left': lambda o: o.expand_selection(-1),
        'Right': lambda o: o.expand_selection(1),
        'Home': lambda o: o.expand_selection(-1000),
        'End': lambda o: o.expand_selection(1000),
    }

    IDENTIFIER_CHARS = u"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_ "

    def __init__(self, handle):
        ShareableActivity.__init__(self, handle)

        self.old_eqs = []
        
        self.ml = MathLib()
        self.parser = AstParser(self.ml)

        # These will result in 'Ans <operator character>' being inserted
        self._chars_ans_diadic = [op[0] for op in self.parser.get_diadic_operators()]
        try:
            self._chars_ans_diadic.remove('-')
        except:
            pass

        self.KEYMAP['multiply'] = self.ml.mul_sym
        self.KEYMAP['divide'] = self.ml.div_sym
        self.KEYMAP['equal'] = self.ml.equ_sym

        self.clipboard = gtk.Clipboard()
        self.select_reason = self.SELECT_SELECT
        self.buffer = u""
        self.showing_version = 0
        self.showing_error = False
        self.ans_inserted = False
        self.show_vars = False

        self.connect("key_press_event", self.keypress_cb)
        self.connect("destroy", self.cleanup_cb)
        self.color = sugar.profile.get_color()

        self.layout = CalcLayout(self)
        self.label_entry = self.layout.label_entry
        self.text_entry = self.layout.text_entry
        self.last_eq_sig = None
        self.last_eqn_textview = None

        self.reset()
        self.layout.show_it()

        self.connect('joined', self._joined_cb)

        self.parser.log_debug_info()

    def ignore_key_cb(self, widget, event):
        return True

    def cleanup_cb(self, arg):
        _logger.debug('Cleaning up...')

    def equation_pressed_cb(self, eqn):
        """Callback for when an equation box is clicked"""

        if isinstance(eqn.result, SVGImage):
            return True

        if len(eqn.label) > 0:
            text = eqn.label
        else:
            # don't insert plain text
            if type(eqn.result) in (types.StringType, types.UnicodeType):
                text = ''
            else:
                text = self.parser.ml.format_number(eqn.result)

        self.button_pressed(self.TYPE_TEXT, text)
        return True

    def set_last_equation(self, eqn):
        """Set the 'last equation' TextView"""

        if self.last_eq_sig is not None:
            self.layout.last_eq.disconnect(self.last_eq_sig)
            self.last_eq_sig = None

        if not isinstance(eqn.result, ParserError):
            self.last_eq_sig = self.layout.last_eq.connect(
                    'button-press-event',
                    lambda a1, a2, e: self.equation_pressed_cb(e), eqn)

        self.layout.last_eq.set_buffer(eqn.create_lasteq_textbuf())

    def set_error_equation(self, eqn):
        """Set equation with error markers. Since set_last_equation implements
        this we can just forward the call."""
        self.set_last_equation(eqn)

    def clear_equations(self):
        """Clear the list of old equations."""
        self.old_eqs = []
        self.showing_version = 0

    def add_equation(self, eq, prepend=False, drawlasteq=False, tree=None):
        """
        Insert equation in the history list and set variable if assignment.
        Input:
            eq: the equation object
            prepend: if True, prepend to list, else append
            drawlasteq: if True, draw in 'last equation' textbox and queue the
            buffer to be added to the history next time an equation is added.
            tree: the parsed tree, this will be used to set the label variable
            so that the equation can be used symbolicaly.
            """
        if eq.equation is not None and len(eq.equation) > 0:
            if prepend:
                self.old_eqs.insert(0, eq)
            else:
                self.old_eqs.append(eq)

            self.showing_version = len(self.old_eqs)

        if self.last_eqn_textview is not None and drawlasteq:
            # Prepending here should be the opposite: prepend -> eqn on top.
            # We always own this equation
            self.layout.add_equation(self.last_eqn_textview, True,
                prepend=not prepend)
            self.last_eqn_textview = None

        own = (eq.owner == self.get_owner_id())
        w = eq.create_history_object()
        w.connect('button-press-event', lambda w, e: self.equation_pressed_cb(eq))
        if drawlasteq:
            self.set_last_equation(eq)

            # SVG images can't be plotted in last equation window
            if isinstance(eq.result, SVGImage):
                self.layout.add_equation(w, own, prepend=not prepend)
            else:
                self.last_eqn_textview = w
        else:
            self.layout.add_equation(w, own, prepend=not prepend)

        if eq.label is not None and len(eq.label) > 0:
            w = self.create_var_textview(eq.label, eq.result)
            if w is not None:
                self.layout.add_variable(eq.label, w)

            if tree is None:
                tree = self.parser.parse(eq.equation)
            self.parser.set_var(eq.label, tree)

    # FIXME: to be implemented
    def process_async(self, eqn):
        """Parse and process an equation asynchronously."""

    def process(self):
        """Parse the equation entered and show the result"""

        s = unicode(self.text_entry.get_text())
        label = unicode(self.label_entry.get_text())
        _logger.debug('process(): parsing %r, label: %r', s, label)
        try:
            tree = self.parser.parse(s)
            res = self.parser.evaluate(tree)
        except ParserError, e:
            res = e
            self.showing_error = True

        if type(res) == types.StringType and res.find('</svg>') > -1:
            res = SVGImage(data=res)

        _logger.debug('Result: %r', res)

        # Check whether assigning this label would cause recursion
        if not isinstance(res, ParserError) and len(label) > 0:
            lastpos = self.parser.get_var_used_ofs(label)
            if lastpos is not None:
                res = RuntimeError(_('Can not assign label: will cause recursion'),
                        lastpos)

# If parsing went ok, see if we have to replace the previous answer
# to get a (more) exact result
        if self.ans_inserted and not isinstance(res, ParserError) \
                and not isinstance(res, SVGImage):
            ansvar = self.format_insert_ans()
            pos = s.find(ansvar)
            if len(ansvar) > 6 and pos != -1:
                s2 = s.replace(ansvar, 'LastEqn')
                _logger.debug('process(): replacing previous answer %r: %r', ansvar, s2)
                tree = self.parser.parse(s2)
                res = self.parser.evaluate(tree)

        eqn = Equation(label, s, res, self.color, self.get_owner_id(), ml=self.ml)

        if isinstance(res, ParserError):
            self.set_error_equation(eqn)
        else:
            self.add_equation(eqn, drawlasteq=True, tree=tree)
            self.send_message("add_eq", value=str(eqn))

            self.parser.set_var('Ans', eqn.result)

            # Setting LastEqn to the parse tree would certainly be faster,
            # however, it introduces recursion problems
            self.parser.set_var('LastEqn', eqn.result)

            self.showing_error = False
            self.ans_inserted = False
            self.text_entry.set_text(u'')
            self.label_entry.set_text(u'')

        return res is not None

    def create_var_textview(self, name, value):
        """Create a gtk.TextView for a variable"""

        reserved = ["Ans", "LastEqn", "help"]
        if name in reserved:
            return None
        w = gtk.TextView()
        w.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.color.get_fill_color()))
        w.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.color.get_stroke_color()))
        w.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        w.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 4)
        w.set_border_window_size(gtk.TEXT_WINDOW_RIGHT, 4)
        w.set_border_window_size(gtk.TEXT_WINDOW_TOP, 4)
        w.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM, 4)
        w.connect('realize', _textview_realize_cb)
        buf = w.get_buffer()

        # TODO Fix for old Sugar 0.82 builds, red_float not available
        bright = (gtk.gdk.color_parse(self.color.get_fill_color()).red_float +
                  gtk.gdk.color_parse(self.color.get_fill_color()).green_float +
                  gtk.gdk.color_parse(self.color.get_fill_color()).blue_float) / 3.0
        if bright < 0.5:
            col = gtk.gdk.color_parse('white')
        else:
            col = gtk.gdk.color_parse('black')

        tag = buf.create_tag(font=CalcLayout.FONT_SMALL_NARROW,
                foreground=col)
        text = '%s:' % (name)
        buf.insert_with_tags(buf.get_end_iter(), text, tag)
        tag = buf.create_tag(font=CalcLayout.FONT_SMALL,
                foreground=col)
        text = '%s' % (str(value))
        buf.insert_with_tags(buf.get_end_iter(), text, tag)

        return w
    
    def clear(self):
        self.text_entry.set_text(u'')
        self.text_entry.grab_focus()
        return True

    def reset(self):
        self.clear()
        return True

##########################################
# Journal functions
##########################################

    def write_file(self, file_path):
        """Write journal entries, Calculate Journal Version (cjv) 1.0"""

        _logger.info(_('Writing to journal (%s)'), file_path)

        f = open(file_path, 'w')
        f.write("cjv 1.0\n")

        sel = self.text_entry.get_selection_bounds()
        pos = self.text_entry.get_position()
        if len(sel) == 0:
            sel = (pos, pos)
            f.write("%s;%d;%d;%d\n" % (self.text_entry.get_text(), pos, sel[0], sel[1]))

# In reverse order
        for eq in self.old_eqs:
            f.write(str(eq))

        f.close()

    def read_file(self, file_path):
        """Read journal entries, version 1.0"""

        _logger.info('Reading from journal (%s)', file_path)

        f = open(file_path, 'r')
        str = f.readline().rstrip("\r\n")   # chomp
        l = str.split()
        if len(l) != 2:
            _logger.error('Unable to determine version')
            return False

        version = l[1]
        if len(version) > 1 and version[0:2] == "1.":
            _logger.info('Reading journal entry (version %s)', version)

            str = f.readline().rstrip("\r\n")
            l = str.split(';')
            if len(l) != 4:
                _logger.error('State line invalid (%s)', str)
                return False

            self.text_entry.set_text(l[0])
            self.text_entry.set_position(int(l[1]))
            if l[2] != l[3]:
                self.text_entry.select_region(int(l[2]), int(l[3]))

            self.clear_equations()
            for str in f:
                eq = Equation(eqnstr=str, ml=self.ml)
                self.add_equation(eq, prepend=False)

            return True
        else:
            _logger.error('Unable to read journal entry, unknown version (%s)', version)
            return False

##########################################
# User interaction functions
##########################################

    def remove_character(self, dir):
        pos = self.text_entry.get_position()
        str = self.text_entry.get_text()
        sel = self.text_entry.get_selection_bounds()
        if len(sel) == 0:
            if pos + dir <= len(self.text_entry.get_text()) and pos + dir >= 0:
                if dir < 0:
                    self.text_entry.delete_text(pos+dir, pos)
                    pos -= 1
                else:
                    self.text_entry.delete_text(pos, pos+dir)
                    pos += 1
        else:
            self.text_entry.delete_text(sel[0], sel[1])
        self.text_entry.grab_focus()
        self.text_entry.set_position(pos) 

    def move_left(self):
        pos = self.text_entry.get_position()
        if pos > 0:
            pos -= 1
            self.text_entry.set_position(pos)
        self.text_entry.grab_focus()
        self.text_entry.set_position(pos) 

    def move_right(self):
        pos = self.text_entry.get_position()
        if pos < len(self.text_entry.get_text()):
            pos += 1
            self.text_entry.set_position(pos)
        self.text_entry.grab_focus()
        self.text_entry.set_position(pos) 

    def label_entered(self):
        if len(self.label_entry.get_text()) > 0:
            return
        pos = self.text_entry.get_position()
        str = self.text_entry.get_text()
        self.label_entry.set_text(str[:pos])
        self.text_entry.set_text(str[pos:])

    def tab_complete(self):

# Get start of variable name
        str = self.text_entry.get_text()
        if len(str) == 0:
            return

        sel = self.text_entry.get_selection_bounds()
        if len(sel) == 0:
            end_ofs = self.text_entry.get_position()
        else:
            end_ofs = sel[0]
        start_ofs = end_ofs - 1
        while start_ofs > 0 and str[start_ofs - 1] in self.IDENTIFIER_CHARS:
            start_ofs -= 1
        if end_ofs - start_ofs <= 0:
            return False
        partial_name = str[start_ofs:end_ofs]
        _logger.debug('tab-completing %s...', partial_name)

# Lookup matching variables
        vars = self.parser.get_names(start=partial_name)
        if len(vars) == 0:
            return False

# Nothing selected, select first match
        if len(sel) == 0:
            name = vars[0]
            self.text_entry.set_text(str[:start_ofs] + name + str[end_ofs:])

# Select next matching variable
        else:
            full_name = str[start_ofs:sel[1]]
            if full_name not in vars:
                name = vars[0]
            else:
                name = vars[(vars.index(full_name) + 1) % len(vars)]
            self.text_entry.set_text(str[:start_ofs] + name + str[sel[1]:])

        self.text_entry.set_position(start_ofs + len(name))
        self.text_entry.select_region(end_ofs, start_ofs + len(name))
        self.select_reason = self.SELECT_TAB
        return True

# Selection related functions

    def expand_selection(self, dir):
#        _logger.info('Expanding selection in dir %d', dir)
        sel = self.text_entry.get_selection_bounds()
        slen = len(self.text_entry.get_text())
        pos = self.text_entry.get_position()
        if len(sel) == 0:
            sel = (pos, pos)
        if dir < 0:
            newpos = max(0, sel[0] + dir)
            self.text_entry.set_position(newpos)   # apparently no such thing as a cursor position during select
            self.text_entry.select_region(newpos, sel[1])
        elif dir > 0:
            newpos = min(sel[1] + dir, slen)
            self.text_entry.set_position(newpos)
            self.text_entry.select_region(sel[0], newpos)
        self.select_reason = self.SELECT_SELECT

    def text_copy(self):
        if self.layout.graph_selected is not None:
            self.clipboard.set_image(self.layout.graph_selected.child.get_pixbuf())
            self.layout.toggle_select_graph(self.layout.graph_selected)
        else:
            str = self.text_entry.get_text()
            sel = self.text_entry.get_selection_bounds()
 #       _logger.info('text_copy, sel: %r, str: %s', sel, str)
            if len(sel) == 2:
                (start, end) = sel
                self.clipboard.set_text(str[start:end])

    def get_clipboard_text(self):
        text = self.clipboard.wait_for_text()
        if text is None:
            return ""
        else:
            return text

    def text_paste(self):
        self.button_pressed(self.TYPE_TEXT, self.get_clipboard_text())

    def text_cut(self):
        self.text_copy()
        self.remove_character(1)

    def keypress_cb(self, widget, event):
        if not self.text_entry.is_focus():
            return

        key = gtk.gdk.keyval_name(event.keyval)
        if event.hardware_keycode == 219:
            if (event.state & gtk.gdk.SHIFT_MASK):
                key = 'divide'
            else:
                key = 'multiply'
        _logger.debug('Key: %s (%r, %r)', key, event.keyval, event.hardware_keycode)

        if event.state & gtk.gdk.CONTROL_MASK:
            if self.CTRL_KEYMAP.has_key(key):
                f = self.CTRL_KEYMAP[key]
                return f(self)
        elif (event.state & gtk.gdk.SHIFT_MASK) and self.SHIFT_KEYMAP.has_key(key):
            f = self.SHIFT_KEYMAP[key]
            return f(self)
        elif unicode(key) in self.IDENTIFIER_CHARS:
            self.button_pressed(self.TYPE_TEXT, key)
        elif self.KEYMAP.has_key(key):
            f = self.KEYMAP[key]
            if type(f) is types.StringType or \
                type(f) is types.UnicodeType:
                self.button_pressed(self.TYPE_TEXT, f)
            else:
                return f(self)

        return True
        
    def get_older(self):
        self.showing_version = max(0, self.showing_version - 1)
        if self.showing_version == len(self.old_eqs) - 1:
            self.buffer = self.text_entry.get_text()
        if len(self.old_eqs) > 0:
            self.text_entry.set_text(self.old_eqs[self.showing_version].equation)
	
    def get_newer(self):
        self.showing_version = min(len(self.old_eqs), self.showing_version + 1)
        if self.showing_version == len(self.old_eqs):
            self.text_entry.set_text(self.buffer)
        else:
            self.text_entry.set_text(self.old_eqs[self.showing_version].equation)

    def add_text(self, input_str):
        self.button_pressed(self.TYPE_TEXT, input_str)

# This function should be split up properly
    def button_pressed(self, str_type, input_str):
        sel = self.text_entry.get_selection_bounds()
        pos = self.text_entry.get_position()

# If selection by tab completion just manipulate end
        if len(sel) == 2 and self.select_reason != self.SELECT_SELECT:
            pos = sel[1]
            sel = ()

        self.text_entry.grab_focus()
        if len(sel) == 2:
            (start, end) = sel
            text = self.text_entry.get_text()
        elif len(sel) != 0:
            _logger.error('button_pressed(): len(sel) != 0 or 2')
            return False

        if str_type == self.TYPE_FUNCTION:
            if len(sel) == 0:
                self.text_entry.insert_text(input_str + '()', pos)
                self.text_entry.set_position(pos + len(input_str) + 1)
            else:
                self.text_entry.set_text(text[:start] + input_str + '(' + text[start:end] + ')' + text[end:])
                self.text_entry.set_position(end + len(input_str) + 2)

        elif str_type == self.TYPE_OP_PRE:
            if len(sel) is 2:
                pos = start
            self.text_entry.insert_text(input_str, pos)
            self.text_entry.set_position(pos + len(input_str))

        elif str_type == self.TYPE_OP_POST:
            if len(sel) is 2:
                pos = end
            elif pos == 0:
                ans = self.format_insert_ans()
                input_str = ans + input_str
                self.ans_inserted = True
            self.text_entry.insert_text(input_str, pos)
            self.text_entry.set_position(pos + len(input_str))

        elif str_type == self.TYPE_TEXT:
            tlen = len(self.text_entry.get_text())
            if len(sel) == 2:
                tlen -= (end - start)

            if tlen == 0 and (input_str in self._chars_ans_diadic) and \
                    self.parser.get_var('Ans') is not None and \
                    type(self.parser.get_var('Ans')) is not str:
                ans = self.format_insert_ans()
                self.text_entry.set_text(ans + input_str)
                self.text_entry.set_position(len(ans) + len(input_str))
                self.ans_inserted = True
            elif len(sel) is 2:
                self.text_entry.set_text(text[:start] + input_str + text[end:])
                self.text_entry.set_position(pos + start - end + len(input_str))
            else:
                self.text_entry.insert_text(input_str, pos)
                self.text_entry.set_position(pos + len(input_str))

        else:
            _logger.error(_('button_pressed(): invalid type'))

    def message_received(self, msg, **kwargs):
        _logger.debug('Message received: %s(%r)', msg, kwargs)

        value = kwargs.get('value', None)
        if msg == "add_eq":
            eq = Equation(eqnstr=str(value), ml=self.ml)
            self.add_equation(eq)
        elif msg == "req_sync":
            data = []
            for eq in self.old_eqs:
                data.append(str(eq))
            self.send_message("sync", value=data)
        elif msg == "sync":
            tmp = []
            self.clear_equations()
            for eq_str in value:
                _logger.debug('receive_message: %s', str(eq_str))
                self.add_equation(Equation(eqnstr=str(eq_str)), ml=self.ml)

    def _joined_cb(self, gobj):
        _logger.debug('Requesting synchronization')
        self.send_message('req_sync')

    def format_insert_ans(self):
        ans = self.parser.get_var('Ans')
        if isinstance(ans, Rational):
            return str(ans)
        elif ans is not None:
            return self.ml.format_number(ans)
        else:
            return ''

def main():
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    t = Calculate(win)
    gtk.main()
    return 0

if __name__ == "__main__":
    main()
