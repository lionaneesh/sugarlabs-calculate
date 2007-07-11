import logging
logging.basicConfig(level=logging.DEBUG,
                    filename='/home/rwh/Calc2.test.log',
                    filemode='w')

from eqnparser import EqnParser
from mathlib import MathLib
import decimal

ml = MathLib()
a = EqnParser()
eq = '2.0 * 1.23e-17 / sin((2+3)*3) * 2^7.5*1.1'
#eq = "(2+3)*3"
res = a.parse(eq)
print 'Eq: \'%s\' ==> %s' % (eq, ml.format_number(res))

a = decimal.Decimal('1234567.89')
print ml.format_number(a)
a = decimal.Decimal('123456.789')
print ml.format_number(a)
a = decimal.Decimal('12345.6789')
print ml.format_number(a)
a = decimal.Decimal('1234.56789')
print ml.format_number(a)
a = decimal.Decimal('123.456789')
print ml.format_number(a)
a = decimal.Decimal('12.3456789')
print ml.format_number(a)
a = decimal.Decimal('1.23456789')
print ml.format_number(a)
a = decimal.Decimal('0.123456789')
print ml.format_number(a)
a = decimal.Decimal('0.0123456789')
print ml.format_number(a)
a = decimal.Decimal('0.00123456789')
print ml.format_number(a)
a = decimal.Decimal('0.000123456789')
print ml.format_number(a)
a = decimal.Decimal('0.0000123456789')
print ml.format_number(a)
a = decimal.Decimal('0.00000123456789')
print ml.format_number(a)
a = decimal.Decimal('0.000000123456789')
print ml.format_number(a)
