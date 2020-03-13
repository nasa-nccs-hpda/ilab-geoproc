import numpy as np
import math
import matplotlib.pyplot as plt

def f(x): return math.log( 1.0 + x*x )
def f1(x): return 2*x / ( 1+ x*x )

X = np.linspace( 0.0, 10.0, 100 )
Y = [ f1(x) for x in X ]

plt.plot( X, Y, linewidth=2.0 )
plt.show()
