# constants.py, constants available in Calculate,
# by Reinier Heeres <reinier@heeres.eu>
# Most of these come from Wikipedia.
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

import math as _math

pi = _math.pi        # 3.1415926535
e = _math.exp(1)     # 2.7182818284590451


class math:
    golden_ratio = 1.61803398874989484820458683436563811


class physics:
    c = 299792458               # Speed of light (in vacuum)
    h = 6.6260689633e-34        # Planck's constant
    hbar = 1.05457162853e-34    # Dirac's constant
    mu0 = 4e-7 * pi             # Magnetic permeability of vacuum
    e0 = 8.854187817e-12        # Electric permeability of vacuum

    Na = 6.022141510e23         # Avogadro's number
    kb = 1.380650524e-23        # Boltmann's constant
    R = 8.31447215              # Gas constant

    c_e = -1.60217648740e-19    # Electron charge
    m_e = 9.109382616e-31       # Electron mass
    m_p = 1.6726217129e-27      # Proton mass
    m_n = 1.6749272928e-27      # Neutron mass
