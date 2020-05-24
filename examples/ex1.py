
"""
x4 = [0.01, 1.0];
x3 = [0.01, 1.0];
x2 = [0.01, 1.0];
x1 = [0.01, 1.0];
(x3^2 > 0.24999999999999994) &&
(x1 - x2 > 0.39999999999999997) && 
(x4*(x3 + x2/x1) - 5.55111512312578e-17 <= x1^2 + 1.11577413974828e-14) &&
((x3^2 < 0.25000000000000006) || (x4*(x3 + x2/x1) + 5.55111512312578e-17 >= x1^2 - 1.11577413974828e-14));
"""

from z3 import *

s = Solver()

x1 = Real('x1')
x2 = Real('x2')
x3 = Real('x3')
x4 = Real('x4')

IC1 = And(x1 >= 0.01, x1 <= 1.0)
IC2 = And(x2 >= 0.01, x2 <= 1.0)
IC3 = And(x3 >= 0.01, x3 <= 1.0)
IC4 = And(x4 >= 0.01, x4 <= 1.0)

y0 = (x3**2 > 0.24999999999999994)
y1 = (x1-x2 > 0.39999999999999997)
y2 = (x1-x2 < 0.4000000000000001)
y3 = (x4*(x3 + x2/x1) - 5.55111512312578e-17 <= x1**2 + 1.11577413974828e-14)
y4 = Or((x3**2 < 0.25000000000000006), (x4*(x3 + x2/x1) + 5.55111512312578e-17 >= x1**2 - 1.11577413974828e-14))

s.add(IC1, IC2, IC3, IC4, y0, y1, y2, y3, y4)
print(s.sexpr())
print(s.check())
print(s.model())
