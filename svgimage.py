# svgimage.py, svg image class by Reinier Heeres <reinier@heeres.eu>
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
#    2007-09-07: rwh, first version

import logging
_logger = logging.getLogger('SVGImage')

import gtk
import rsvg

class SVGImage:

    def __init__(self, fn=None, data=None):
        if fn is not None:
            self.load(fn)
        elif data is not None:
            self.load_data(data)

    def get_image(self):
        return self._image

    def get_svg_data(self):
        return self._svg_data

    def render_svg(self):
        self._handle = rsvg.Handle(data=self._svg_data)
        self._pixbuf = self._handle.get_pixbuf()
        self._image = gtk.Image()
        self._image.set_from_pixbuf(self._pixbuf)
        self._image.set_alignment(0.5, 0)
        return self._image
        
    def load(self, fn):
        f = open(fn, 'rb')
        self._svg_data = f.read()
        f.close()
        return self.render_svg()

    def load_data(self, svgdat):
        self._svg_data = svgdat
        return self.render_svg()
