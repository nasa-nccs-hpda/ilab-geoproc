import matplotlib.pyplot as plt
import datetime, math
import numpy as np
from geoproc.covid.smooth import smooth
from geoproc.covid.cvgrowth import infection_data

d0 = datetime.datetime(2020,3,7)
dr = 3.0
npoints = 15


def gf( y0, y1 ):
    return math.log( y1/y0, 2.0 )


V = [ ]
D = [ ]
for i in range(0,len(infection_data)-1):
    f = gf( infection_data[i], infection_data[i+1] )
    V.append( f )
    d = d0 + datetime.timedelta(days=i)
    D.append( d )

fig, axs = plt.subplots(1,2)
# V1 = smooth( np.array( V ) )[1:]
V1 = np.array( V )
V2 = [ 1/v for v in V1 ]

ax = axs[0]
ax.set_title( "Covid-19 USA Infection Growth Rate", fontsize=20 )
ax.set_xlabel('Date', fontsize=14)
ax.ticklabel_format(axis="y",style="plain")
ax.set_ylabel( 'Doubling Frequency (1/days)', fontsize=14 )
ax.plot( D, V1, '-', color="red", lw=2 )
ax.legend()


ax = axs[1]
ax.set_title( "Covid-19 USA Infection Doubling Period", fontsize=20 )
ax.set_xlabel('Date', fontsize=14)
ax.ticklabel_format(axis="y",style="plain")
ax.set_ylabel( 'Doubling Period (days)', fontsize=14 )
ax.plot( D, V2, '-', color="blue", lw=2 )
ax.legend()

plt.show()
