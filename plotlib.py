# plotlib.py, svg plot generator by Reinier Heeres <reinier@heeres.eu>
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
#    2007-09-04: rwh, first version

import types

import logging
_logger = logging.getLogger('PlotLib')

class PlotLib:
    """Class to generate an svg plot for a function.
    Evaluation of values is done using the EqnParser class."""

    def __init__(self, parser):
        self.parser = parser

        self.svg_data = ""
        self.set_size(0, 0)

    def set_size(self, width, height):
        self.width = width
        self.height = height

    def get_svg(self):
        return self.svg_data

    def evaluate(self, eqn, var, range, points=100):
        x_old = self.parser.get_var(var)

        if type(eqn) in (types.StringType, types.UnicodeType):
            eqn = self.parser.parse(eqn)

        res = []
        d = float((range[1] - range[0])) / (points - 1)
        x = range[0]
        while points > 0:
            self.parser.set_var(var, x)
            ret = self.parser.evaluate(eqn)
            if ret is not None:
                v = float(ret)
            else:
                v = 0
            res.append((x, v))
            x += d
            points -= 1

        self.parser.set_var(var, x_old)
        return res

    def create_image(self):
        self.svg_data = '<?xml version="1.0" standalone="no"?>\n'
        self.svg_data += '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        self.svg_data += '<svg width="%d" height="%d" version="1.1" xmlns="http://www.w3.org/2000/svg">\n' % (self.width, self.height)

    def finish_image(self):
        self.svg_data += '</svg>'

    def plot_line(self, c0, c1, col):
        c0 = self.rcoords_to_coords(c0)
        c1 = self.rcoords_to_coords(c1)
        self.svg_data += '<line style="stroke:%s;stroke-width:1" x1="%f" y1="%f" x2="%f" y2="%f" />\n' % (col, c0[0], c0[1], c1[0], c1[1])

    def plot_polyline(self, coords, col):
        self.svg_data += '<polyline style="fill:none;stroke:%s;stroke-width:1" points="' % (col)
        for c in coords:
            c = self.rcoords_to_coords(c)
            self.svg_data += '%f,%f ' % (c[0], c[1])
        self.svg_data += '" />\n'

    def add_text(self, c, text, rotate=0):
        if type(text) is types.UnicodeType:
            text = text.encode('utf-8')
        c = self.rcoords_to_coords(c)

        self.svg_data += '<text x="%f" y="%f"' % (c[0], c[1])
        if rotate != 0:
            self.svg_data += ' transform="rotate(%d)"' % (rotate)

        self.svg_data += '>%s</text>\n' % (text)

    def determine_bounds(self, vals):
        self.minx = self.miny = 1e99
        self.maxx = self.maxy = -1e99
        for (x, y) in vals:
            self.minx = min(float(x), self.minx)
            self.miny = min(float(y), self.miny)
            self.maxx = max(float(x), self.maxx)
            self.maxy = max(float(y), self.maxy)

        if self.minx == self.maxx:
            xYspace = 0.5
        else:
            x_space = 0.02 * (self.maxx - self.minx)
        self.minx -= x_space
        self.maxx += x_space

        if self.miny == self.maxy:
            y_space = 0.5
        else:
            y_space = 0.02 * (self.maxy - self.miny)
        self.miny -= y_space
        self.maxy += y_space

    def rcoords_to_coords(self, pair):
        """Convert fractional coordinates to image coordinates"""
        return (pair[0] * self.width, pair[1] * self.height)

    def vals_to_rcoords(self, pair):
        """Convert values to fractional coordinates"""
        ret = (0.1 + (pair[0] - self.minx) / (self.maxx - self.minx) * 0.8, \
               0.9 - (pair[1] - self.miny) / (self.maxy - self.miny) * 0.8)
        return ret

    def add_curve(self, vals):
        self.determine_bounds(vals)

        c = []
        for v in vals:
            c.append(self.vals_to_rcoords(v))
#        print 'coords: %r' % c

        self.plot_polyline(c, "blue")

    def get_label_vals(self, startx, endx, n, opts=()):
        """Return label values"""
        range = endx - startx
        logrange = log(range)
        haszero = (startx < 0 & endx < 0)

    def draw_axes(self, labelx, labely):
        self.plot_line((0.08, 0.92), (0.92, 0.92), "black")
        self.add_text((0.50, 0.98), labelx)

        self.plot_line((0.08, 0.08), (0.08, 0.92), "black")
        self.add_text((-0.50, 0.065), labely, rotate=-90)

    def export_plot(self, fn):
        f = open(fn, "w")
        f.write(self.svg_data)
        f.close()

    def plot(self, eqn, **kwargs):
        '''
        Plot function <eqn>.

        kwargs can contain: 'points'

        The last item in kwargs is interpreted as the variable that should
        be varied.
        '''

        _logger.debug('plot(): %r, %r', eqn, kwargs)

        if 'points' in kwargs:
            points = kwargs['points']
            del kwargs['points']
        else:
            points = 100

        if len(kwargs) > 1:
            _logger.error('Too many variables specified')
            return None

        for var, range in kwargs.iteritems():
            pass
        _logger.info('Plot range for var %s: %r', var, range)

        self.set_size(250, 250)
        self.create_image()

        # FIXME: should use equation as label
        self.draw_axes(var, 'f(x)')

        vals = self.evaluate(eqn, var, range, points=points)
#        print 'vals: %r' % vals
        self.add_curve(vals)

        self.finish_image()

#        self.export_plot("/tmp/calculate_graph.svg")
        svg = self.get_svg()
        if type(svg) is types.UnicodeType:
            return svg.encode('utf-8')
        else:
            return svg
