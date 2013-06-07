# plotlib.py, svg plot generator by Reinier Heeres <reinier@heeres.eu>
# Copyright (C) 2012 Aneesh Dogra <lionaneesh@gmail.com>
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

USE_MPL = True

def format_float(x):
    return ('%.2f' % x).rstrip('0').rstrip('.')

class _PlotBase:
    """Class to generate an svg plot for a function.
    Evaluation of values is done using the EqnParser class."""

    def __init__(self, parser):
        self.svg_data = ""
        self.parser = parser

    def get_svg(self):
        return self.svg_data

    def set_svg(self, data):
        self.svg_data = data

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

    def export_plot(self, fn):
        f = open(fn, "w")
        f.write(self.get_svg())
        f.close()

    def produce_plot(self, vals, *args, **kwargs):
        '''Function to produce the actual plot, override.'''
        pass

    def plot(self, eqn, **kwargs):
        '''
        Plot function <eqn>.

        kwargs can contain: 'points'

        The last item in kwargs is interpreted as the variable that should
        be varied.
        '''

        _logger.debug('plot(): %r, %r', eqn, kwargs)

        if len(kwargs) == 0:
            _logger.error('No variables specified.')
            return None

        points = kwargs.pop('points', 100)
        if len(kwargs) > 1:
            _logger.error('Too many variables specified')
            return None

        for var, range in kwargs.iteritems():
            _logger.info('Plot range for var %s: %r', var, range)

        vals = self.evaluate(eqn, var, range, points=points)
        _logger.debug('vals are %r', vals)
        svg = self.produce_plot(vals, xlabel=var, ylabel='f(x)')
        _logger.debug('SVG Data: %s', svg)
        self.set_svg(svg)

#        self.export_plot("/tmp/calculate_graph.svg")
        if type(svg) is types.UnicodeType:
            return svg.encode('utf-8')
        else:
            return svg

class CustomPlot(_PlotBase):

    def __init__(self, parser):
        _PlotBase.__init__(self, parser)

        self.set_size(0, 0)

    def set_size(self, width, height):
        self.width = width
        self.height = height

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
            x_space = 0.5
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
        ret = (0.1 + (pair[0] - self.minx) / (self.maxx - self.minx) * 0.8,
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

    def draw_axes(self, labelx, labely, val):
        """Draw axes on the plot."""
        F = 0.8
        NOL = 4 # maximum no of labels

        y_coords = sorted([i[1] for i in val])
        x_coords = sorted([i[0] for i in val])

        max_y = max(y_coords)
        min_y = min(y_coords)

        max_x = max(x_coords)
        min_x = min(x_coords)

        # X axis
        interval = len(val)/(NOL - 1)
        self.plot_line((0.11, 0.89), (0.92, 0.89), "black")
        if max_x != min_x:
            self.add_text((0.11 + min_x + F * 0, 0.93), format_float(min_x))
            plot_index = interval
            while plot_index <= len(val) - interval:
                self.add_text((0.11 + F * abs(x_coords[plot_index] - min_x) / \
                               abs(max_x - min_x), 0.93),
                              format_float(x_coords[plot_index]))
                plot_index += interval
            self.add_text((0.11 + F * 1, 0.93), format_float(max_x))
        else:
            self.add_text((0.5 , 0.93), format_float(min_x))

        self.add_text((0.50, 0.98), labelx)

        # Y axis
        interval = float(max_y - min_y)/(NOL - 1)
        self.plot_line((0.11, 0.08), (0.11, 0.89), "black")
        # if its a constant function we only need to plot one label
        if min_y == max_y:
            self.add_text((-0.50, 0.10), format_float(min_y), rotate=-90)        
        else:
            self.add_text((-0.90, 0.10), format_float(min_y), rotate=-90)        
            plot_value = min_y + interval
            while plot_value <= max_y - interval:
                self.add_text((-(0.91 - F * abs(plot_value - min_y) / \
                               abs(max_y - min_y)), 0.10),
                              format_float(plot_value), rotate=-90)
                plot_value += interval
            self.add_text((-(0.89 - F), 0.10), format_float(max_y), rotate=-90)

        self.add_text((-0.50, 0.045), labely, rotate=-90)

    def produce_plot(self, vals, *args, **kwargs):
        """Produce an svg plot."""

        self.set_size(250, 250)
        self.create_image()

        self.draw_axes(kwargs.get('xlabel', ''), kwargs.get('ylabel', ''), vals)

        self.add_curve(vals)

        self.finish_image()

        return self.svg_data

class MPLPlot(_PlotBase):

    def __init__(self, parser):
        _PlotBase.__init__(self, parser)

    def produce_plot(self, vals, **kwargs):
        x = [c[0] for c in vals]
        y = [c[1] for c in vals]

        fig = pylab.figure()
        fig.set_size_inches(5, 5)
        ax = fig.add_subplot(111)

        ax.plot(x, y, 'r-')

        ax.set_xlabel(kwargs.get('xlabel', ''))
        ax.set_ylabel(kwargs.get('ylabel', ''))

        data = StringIO.StringIO()
        fig.savefig(data)
        return data.getvalue()

if USE_MPL:
    try:
        import matplotlib as mpl
        mpl.use('svg')
        from matplotlib import pylab
        import StringIO
        Plot = MPLPlot
        _logger.debug('Using matplotlib as plotting back-end')
    except ImportError:
        USE_MPL = False

if not USE_MPL:
    Plot = CustomPlot
    _logger.debug('Using custom plotting back-end')
