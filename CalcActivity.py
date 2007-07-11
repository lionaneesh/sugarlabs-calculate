# CalcActivity.py, sugar calculator, by Reinier Heeres <reinier@heeres.eu>
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
_logger = logging.getLogger('calc-activity')

import gobject
import pygtk
pygtk.require('2.0')
import gtk
import pango

from sugar.activity import activity

from layout import CalcLayout
from mathlib import MathLib
from eqnparser import EqnParser

class CalcActivity(activity.Activity):

    TYPE_FUNCTION = 1
    TYPE_OP_PRE = 2
    TYPE_OP_POST = 3
    TYPE_TEXT = 4

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.set_title("Calc2")
        self.connect("key_press_event", self.keypress_cb)
        self.connect("destroy", self.cleanup_cb)

        self.layout = CalcLayout(self)
        self.label_entry = self.layout.label_entry
        self.text_entry = self.layout.text_entry
        self.history = self.layout.history

        self.reset()

        self.parser = EqnParser()
        self.ml = MathLib()

    def ignore_key_cb(self, widget, event):
        return True

    def cleanup_cb(self, arg):
        _logger.debug('Cleaning up...')
        
    def process(self):
        s = self.text_entry.get_text()
        label = self.label_entry.get_text()
        _logger.debug('process(): parsing \'%s\', label: \'%s\'', s, label)

        buf = self.history.get_buffer()

        res = self.parser.parse(s)
        if res is not None:
            buf.insert(buf.get_start_iter(), '\t= ' + self.ml.format_number(res) + '\n')
            self.text_entry.set_text('')
            self.parser.set_var('Ans', self.ml.format_number(res))

            if len(label) > 0:
                self.label_entry.set_text('')
                self.parser.set_var(label, s)

        else:
            pos = self.parser.get_error_offset()
            self.text_entry.set_position(pos)
            buf.insert(buf.get_start_iter(), '\tError at %d\n' % pos)

        if len(label) > 0:
            buf.insert(buf.get_start_iter(), label + ': ' + s + '\n')
        else:
            buf.insert(buf.get_start_iter(), s + '\n')

        return res is not None

    def clear(self):
        _logger.debug('Clearing...')
        self.text_entry.set_text('')
        return True

    def reset(self):
        _logger.debug('Resetting...')
        self.text_entry.grab_focus()
        return True

##########################################
# User interaction functions
##########################################

    def add_text(self, c):
        pos = self.text_entry.get_position()
        self.text_entry.insert_text(c, pos)
        self.text_entry.grab_focus()
        self.text_entry.set_position(pos + len(c))

    def remove_character(self, dir):
        pos = self.text_entry.get_position()
        print 'Position: %d, dir: %d, len: %d' % (pos, dir, len(self.text_entry.get_text()))
        if pos + dir <= len(self.text_entry.get_text()) and pos + dir >= 0:
            if dir < 0:
                self.text_entry.delete_text(pos+dir, pos)
            else:
                self.text_entry.delete_text(pos, pos+dir)

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

    def keypress_cb(self, widget, event):
        if self.label_entry.is_focus():
            return

        key = gtk.gdk.keyval_name(event.keyval)
        _logger.debug('Key: %s (%r)', key, event.keyval)

        allowed_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
        if key in allowed_chars:
            self.add_text(key)

        keymap = {
            'Return': lambda: self.process(),
            'period': '.',
            'equal': '=',
            'plus': '+',
            'minus': '-',
            'asterisk': '*',
            'slash': '/',
            'BackSpace': lambda: self.remove_character(-1),
            'Delete': lambda: self.remove_character(1),
            'parenleft': '(',
            'parenright': ')',
            'exclam': '!',
            'ampersand': '&',
            'bar': '|',
            'asciicircum': '^',
            'less': '<',
            'greater': '>',
            'Left': lambda: self.move_left(),
            'Right': lambda: self.move_right(),
            'colon': lambda: self.label_entered()
        }
        if keymap.has_key(key):
            f = keymap[key]
            if type(f) is types.StringType:
                self.add_text(f)
            else:
                return f()

        return True

    def button_pressed(self, type, str):
        sel = self.text_entry.get_selection_bounds()
        pos = self.text_entry.get_position()
        self.text_entry.grab_focus()
        if len(sel) == 2:
            (start, end) = sel
            text = self.text_entry.get_text()
        elif len(sel) != 0:
            _logger.error('button_pressed(): len(sel) != 0 or 2')
            return False

        if type == self.TYPE_FUNCTION:
            if sel is ():
                self.text_entry.insert_text(str + '()', pos)
                self.text_entry.set_position(pos + len(str) + 1)
            else:
                self.text_entry.set_text(text[:start] + str + '(' + text[start:end] + ')' + text[end:])
                if pos > end:
                    self.text_entry.set_position(pos + len(str) + 2)
                elif pos > start:
                    self.text_entry.set_position(pos + len(str) + 1)

        elif type == self.TYPE_OP_PRE:
            if len(sel) is 2:
                pos = start
            self.text_entry.insert_text(str, pos)
            self.text_entry.set_position(pos + len(str))

        elif type == self.TYPE_OP_POST:
            if len(sel) is 2:
                pos = end
            self.text_entry.insert_text(str, pos)
            self.text_entry.set_position(pos + len(str))

        elif type == self.TYPE_TEXT:
            if len(sel) is 2:
                self.text_entry.set_text(text[:start] + str + text[end:])
                self.text_entry.set_position(pos + start - end + len(str))
            else:
                self.text_entry.insert_text(str, pos)
                self.text_entry.set_position(pos + len(str))

        else:
            _logger.error('CalcActivity.button_pressed(): invalid type')

def main():
    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    t = Calc(win)
    gtk.main()
    return 0

if __name__ == "__main__":
    main()
