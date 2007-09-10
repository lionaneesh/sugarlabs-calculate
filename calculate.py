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
from sugar.presence import presenceservice
import sugar.profile
from sugar.graphics.icon import CanvasIcon
from sugar.graphics.xocolor import XoColor

from sharedstate.sharedstate import SharingHelper

from layout import CalcLayout
from mathlib import MathLib
from eqnparser import EqnParser
from svgimage import SVGImage

class Equation:
    def __init__(self, label=None, eqn=None, res=None, col=None, owner=None, str=None):
        if str is not None:
            self.parse(str)
        elif eqn is not None:
            self.set(label, eqn, res, col, owner)

    def set(self, label, eqn, res, col, owner):
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
        str = str.rstrip("\r\n")
        l = str.split(';')
        if len(l) != 5:
            _logger.error('Equation.parse() string invalid (%s)', str)
            return False

        if l[2].startswith("<svg>"):
            l[2] = SVGImage(data=base64.b64decode(l[2][5:]))

        self.set(l[0], l[1], l[2], XoColor(color_string=l[3]), l[4])

class Calculate(activity.Activity):

    TYPE_FUNCTION = 1
    TYPE_OP_PRE = 2
    TYPE_OP_POST = 3
    TYPE_TEXT = 4
    
    FONT_SMALL = "sans 10"
    FONT_SMALL_NARROW = "sans italic 10"
    FONT_BIG = "sans bold 14"
    FONT_BIG_NARROW = "sans italic 14"
    FONT_BIGGER = "sans bold 18"

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
    }

    SHIFT_KEYMAP = {
        'Left': lambda o: o.expand_selection(-1),
        'Right': lambda o: o.expand_selection(1),
        'Home': lambda o: o.expand_selection(-1000),
        'End': lambda o: o.expand_selection(1000),
    }

    IDENTIFIER_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_ "

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.helper_old_eqs = []
        
        self.ml = MathLib()
        self.parser = EqnParser(self.ml)

        self.clipboard = ""
        self.select_reason = self.SELECT_SELECT
        self.buffer = ""
        self.showing_version = 0
        self.showing_error = False
        self.show_vars = False

        self.set_title("Calculate")
        self.connect("key_press_event", self.keypress_cb)
        self.connect("destroy", self.cleanup_cb)
        self.color = sugar.profile.get_color()
##        self.icon = CanvasIcon(
##            icon_name = 'theme:stock-buddy',
##            xo_color = XoColor(self.color))     

        self.layout = CalcLayout(self)
        self.label_entry = self.layout.label_entry
        self.text_entry = self.layout.text_entry
        self.history = self.layout.history
        self.last_eq = self.layout.last_eq.get_buffer()

        self.presence = presenceservice.get_instance()
        self.owner = self.presence.get_owner()
        self.owner_id = str(self.owner._properties["nick"])
        _logger.debug('Owner_id: %s', self.owner_id)

        options = {
            'receive_message': self.receive_message,
            'on_connect': lambda: self.helper.send_message("req_sync", "")
        }
        self.helper = SharingHelper(self, opt=options)
        self.helper.create_shared_object('old_eqs',
                                         {'changed': lambda x: self.buddy_old_eqs_cb(),
                                          'type': 'python'},
                                         iv = [])
        self.helper.create_shared_object('vars',
                                         {'changed': lambda x: self.buddy_vars_cb(),
                                          'type': 'python'},
                                         iv = [])

        _logger.info('Available functions:')
        for f in self.parser.get_function_names():
            _logger.info('\t%s', f)

        self.reset()
        self.layout.show_it()

    def ignore_key_cb(self, widget, event):
        return True

    def cleanup_cb(self, arg):
        _logger.debug('Cleaning up...')

    def equation_pressed_cb(self, n):
        """Callback for when an equation box is clicked"""
        if len(self.helper_old_eqs) <= n:
            return True
        if len(self.helper_old_eqs[n].label) > 0:
            text = self.helper_old_eqs[n].label
        else:
            text = self.helper_old_eqs[n].equation
        self.button_pressed(self.TYPE_TEXT, text)
        return True

    def format_last_eq_buf(self, buf, res, offset):
        eq_start = buf.get_start_iter()
        eq_middle = buf.get_iter_at_line(1)
        eq_end = buf.get_end_iter()
        buf.apply_tag(buf.create_tag(font=self.FONT_BIG_NARROW),
            eq_start, eq_middle)
        buf.apply_tag(buf.create_tag(font=self.FONT_BIGGER,
            justification=gtk.JUSTIFY_RIGHT), eq_middle, eq_end)

        if res is None:
            eq_start.forward_chars(offset)
            end = self.last_eq.get_start_iter()
            end.forward_chars(offset+1)
            self.last_eq.apply_tag(self.last_eq.create_tag(foreground='#FF0000'),
                eq_start, end)
            self.last_eq.apply_tag(self.last_eq.create_tag(foreground='#FF0000'),
                eq_middle, eq_end)

    def set_last_equation(self, eqn):
        text = ""
        if len(eqn.label) > 0:
            text += eqn.label + ': ' + eqn.equation
            offset = len(eqn.label) + 2
        else:
            text += eqn.equation
            offset = 0

        if eqn.result is not None:
            if isinstance(eqn.result, SVGImage):
                pass
            else:
                text += '\n= ' + self.ml.format_number(eqn.result)
                self.parser.set_var('Ans', self.ml.format_number(eqn.result))
                if len(eqn.label) > 0:
                    self.parser.set_var(eqn.label, eqn.equation)
            self.text_entry.set_text('')
            self.label_entry.set_text('')
        else:
            pos = self.parser.get_error_offset()
            if pos == len(text) - 1:
                text += '_'
            offset += pos
            text += '\nError at %d' % pos

        self.last_eq.set_text(text)
        self.format_last_eq_buf(self.last_eq, eqn.result, offset)

    def set_error_equation(self, eqn):
        self.set_last_equation(eqn)

    def insert_equation(self, eq):
        tmp = self.helper_old_eqs
        tmp.insert(0, eq)
        self.helper_old_eqs = tmp

    def process(self):
        s = self.text_entry.get_text()
        label = self.label_entry.get_text()
        _logger.debug('process(): parsing \'%s\', label: \'%s\'', s, label)
        res = self.parser.parse(s)
        if type(res) == types.StringType and res.find('</svg>') > -1:
            res = SVGImage(data=res)
        eqn = Equation(label, s, res, self.color, self.owner_id)

# Result ok
        if res is not None:
            self.insert_equation(eqn)
            self.helper.send_message("add_eq", str(eqn))
            self.showing_error = False

# Show error
        else:
            self.set_error_equation(eqn)
            self.showing_error = True

        self.refresh_bar()

        return res is not None

    def refresh_bar(self):
        _logger.debug('Refreshing right bar...')
        if self.layout.varbut.selected == 0:
            self.refresh_history()
        else:
            self.refresh_vars()

    def buddy_old_eqs_cb(self):
        self.refresh_bar()
    
    def format_var_buf(self, buf):
        iter_start = buf.get_start_iter()
        iter_end = buf.get_end_iter()
        buf.apply_tag(buf.create_tag(font=self.FONT_SMALL_NARROW),
            iter_start, iter_end)
        col = self.color.get_fill_color()
        buf.apply_tag(buf.create_tag(foreground=col), iter_start, iter_end)

    def buddy_vars_cb(self):
        self.refresh_bar()

    def refresh_vars(self):
        list = []
        for name, value in self.parser.get_vars():
            if name == "Ans":
                continue
            w = gtk.TextView()
            b = w.get_buffer()
            b.set_text(name + ":\t" + str(value))
            self.format_var_buf(b)
            list.append(w)
        self.layout.show_history(list)

    def format_history_buf(self, buf, eq):
        iter_start = buf.get_start_iter()
        iter_colon = buf.get_start_iter()
        iter_end = buf.get_end_iter()
        iter_middle = buf.get_iter_at_line(1)
        try:
            pos = buf.get_text(iter_start, iter_end).index(':')
            iter_colon.forward_chars(pos)
        except:
            buf.apply_tag(buf.create_tag(font=self.FONT_SMALL),
                          iter_start, iter_middle)
        else:

            buf.apply_tag(buf.create_tag(font=self.FONT_SMALL_NARROW),
                          iter_start, iter_colon)
            buf.apply_tag(buf.create_tag(font=self.FONT_SMALL),
                          iter_colon, iter_middle)
            
        buf.apply_tag(buf.create_tag(font=self.FONT_BIG,
            justification=gtk.JUSTIFY_RIGHT), iter_middle, iter_end)
        col = eq.color.get_fill_color()
        buf.apply_tag(buf.create_tag(foreground=col), iter_start, iter_end)
    
    def refresh_history(self):
        list = []

        i = 1
        if self.showing_error:
            last_eq_drawn = True
        else:
            last_eq_drawn = False
        for e in self.helper_old_eqs:

            if not last_eq_drawn and e.owner == self.owner_id:
                self.set_last_equation(e)
                last_eq_drawn = True
                if not isinstance(e.result, SVGImage):
                    continue

# Skip if only drawing own equations
            if self.layout.minebut.selected == 1 and e.owner != self.ownder_id:
                continue

            if isinstance(e.result, SVGImage):
                w = e.result.get_image()

            else:
                text = ""
                if len(e.label) > 0:
                    text += str(e.label) + ": "
                r = self.ml.format_number(e.result)
                text += str(e.equation) + "\n=" + r
                w = gtk.TextView()
                w.connect('button-press-event', lambda w, e, j: self.equation_pressed_cb(j), i)
                b = w.get_buffer()
##                b.modify_bg(gtk.STATE_ACTIVE | gtk.STATE_NORMAL,
##                gtk.gdk.color_parse(e.color.get_fill_color())
                b.set_text(text)
                self.format_history_buf(b, e)

            list.append(w)
            i += 1

        self.layout.show_history(list)

    def clear(self):
        self.text_entry.set_text('')
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

        _logger.info('Writing to journal (%s)', file_path)

        f = open(file_path, 'w')
        f.write("cjv 1.0\n")

        sel = self.text_entry.get_selection_bounds()
        pos = self.text_entry.get_position()
        if len(sel) == 0:
            sel = (pos, pos)
            f.write("%s;%d;%d;%d\n" % (self.text_entry.get_text(), pos, sel[0], sel[1]))

        for eq in self.helper_old_eqs:
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

            eqs = []
            for str in f:
                eq = Equation(str=str)
                if eq.equation is not None and len(eq.equation) > 0:
                    eqs.append(eq)
                    if eq.label is not None and len(eq.label) > 0:
                        self.parser.set_var(eq.label, eq.result)
            self.helper_old_eqs = eqs

            self.refresh_bar()

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
                else:
                    self.text_entry.delete_text(pos, pos+dir)
        else:
            self.text_entry.delete_text(sel[0], sel[1])

    def move_left(self):
        pos = self.text_entry.get_position()
        if pos > 0:
            self.text_entry.set_position(pos - 1)

    def move_right(self):
        pos = self.text_entry.get_position()
        if pos < len(self.text_entry.get_text()):
            self.text_entry.set_position(pos + 1)

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
        vars = self.parser.get_var_names(start=partial_name)
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
        str = self.text_entry.get_text()
        sel = self.text_entry.get_selection_bounds()
 #       _logger.info('text_copy, sel: %r, str: %s', sel, str)
        if len(sel) == 2:
            (start, end) = sel
            self.clipboard = str[start:end]

    def text_paste(self):
        self.button_pressed(self.TYPE_TEXT, self.clipboard)

    def text_cut(self):
        self.text_copy()
        self.remove_character(1)

    def keypress_cb(self, widget, event):
        if self.label_entry.is_focus() or \
            self.toolbox.get_activity_toolbar().title.is_focus():
            return

        key = gtk.gdk.keyval_name(event.keyval)
        _logger.debug('Key: %s (%r)', key, event.keyval)

        if (event.state & gtk.gdk.CONTROL_MASK) and self.CTRL_KEYMAP.has_key(key):
            f = self.CTRL_KEYMAP[key]
            return f(self)
        elif (event.state & gtk.gdk.SHIFT_MASK) and self.SHIFT_KEYMAP.has_key(key):
            f = self.SHIFT_KEYMAP[key]
            return f(self)
        elif key in self.IDENTIFIER_CHARS:
            self.button_pressed(self.TYPE_TEXT, key)
        elif self.KEYMAP.has_key(key):
            f = self.KEYMAP[key]
            if type(f) is types.StringType:
                self.button_pressed(self.TYPE_TEXT, f)
            else:
                return f(self)

        return True
	
    def get_older(self):
        self.showing_version = min(len(self.helper_old_eqs), self.showing_version + 1)
        if self.showing_version == 1:
            self.buffer = self.text_entry.get_text()
        self.text_entry.set_text(self.helper_old_eqs[self.showing_version - 1].equation)
        
    def get_newer(self):
        self.showing_version = max(0, self.showing_version - 1)
        if self.showing_version == 0:
            self.text_entry.set_text(self.buffer)
            return
        self.text_entry.set_text(self.helper_old_eqs[self.showing_version - 1].equation)

    def add_text(self, str):
        self.button_pressed(self.TYPE_TEXT, str)

# This function should be split up properly
    def button_pressed(self, type, str):
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

        if type == self.TYPE_FUNCTION:
            if len(sel) == 0:
                self.text_entry.insert_text(str + '()', pos)
                self.text_entry.set_position(pos + len(str) + 1)
            else:
                self.text_entry.set_text(text[:start] + str + '(' + text[start:end] + ')' + text[end:])
                self.text_entry.set_position(end + len(str) + 2)

        elif type == self.TYPE_OP_PRE:
            if len(sel) is 2:
                pos = start
            self.text_entry.insert_text(str, pos)
            self.text_entry.set_position(pos + len(str))

        elif type == self.TYPE_OP_POST:
            if len(sel) is 2:
                pos = end
            elif pos == 0:
                ans = self.parser.ml.format_number(self.parser.get_var('Ans'))
                str = ans + str
            self.text_entry.insert_text(str, pos)
            self.text_entry.set_position(pos + len(str))

        elif type == self.TYPE_TEXT:
            tlen = len(self.text_entry.get_text())
            if len(sel) == 2:
                tlen -= (end - start)

            if tlen == 0 and (str in self.parser.get_diadic_operators() \
                    or str in self.parser.get_post_operators()):
                ans = self.parser.ml.format_number(self.parser.get_var('Ans'))
                self.text_entry.set_text(ans + str)
                self.text_entry.set_position(3 + len(str))
            elif len(sel) is 2:
                self.text_entry.set_text(text[:start] + str + text[end:])
                self.text_entry.set_position(pos + start - end + len(str))
            else:
                self.text_entry.insert_text(str, pos)
                self.text_entry.set_position(pos + len(str))

        else:
            _logger.error('button_pressed(): invalid type')

    def receive_message(self, msg, val):
        if msg == "add_eq":
            eq = Equation(str=str(val))
            self.insert_equation(eq)
            self.refresh_bar()
        elif msg == "req_sync":
            data = []
            for eq in self.helper_old_eqs:
                data.append(str(eq))
            self.helper.send_message("sync", data)
        elif msg == "sync":
            tmp = []
            for eq_str in val:
                _logger.info('receive_message: %s', str(eq_str))
                tmp.append(Equation(str=str(eq_str)))
            self.helper_old_eqs = tmp
            self.refresh_bar()

def main():
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    t = Calculate(win)
    gtk.main()
    return 0

if __name__ == "__main__":
    main()
