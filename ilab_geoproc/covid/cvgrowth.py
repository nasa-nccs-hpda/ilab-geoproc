import matplotlib.pyplot as plt
import datetime

d0 = datetime.datetime(2020,3,7)
dr = 3.0
npoints = 15
infection_data = [ 297, 423, 647, 937, 1215, 1629, 1896, 2234, 3487, 4226, 7038, 10442, 15219, 18747, 24583, 33404, 44183, 54453, 68440, 85356, 103321, 122653, 140904, 163539, 186101, 213144, 239279, 277205, 304826, 330891, 374329, 395001, 427460, 459165, 492416 ]

V = []
D = []
v = infection_data[0]
for i in range(0,npoints):
    V.append( v )
    d = d0 + datetime.timedelta(days=3*i)
    D.append( d )
    v = v * 2

V1 = [ ]
D1 = []
for i in range(0,len(infection_data)):
    V1.append( infection_data[i] )
    d = d0 + datetime.timedelta(days=i)
    D1.append( d )

fig, ax = plt.subplots()
ax.set_title( "Covid-19 USA Infection Rate", fontsize=20 )
ax.set_xlabel('Date', fontsize=14)
ax.ticklabel_format(axis="y",style="plain")
ax.set_ylabel( 'Number of Infections', fontsize=14 )
ax.set_yscale('log')
ax.plot( D, V, '--', color="blue", lw=2, label="Worst Case projection (from 3/7/2020)" )
ax.plot( D1, V1, '-', color="red", lw=2, label="Confirmed USA cases" )
ax.legend()
plt.show()


V1 = [ ]
D1 = []
for i in range(0,len(infection_data)):
    V1.append( infection_data[i] )
    d = d0 + datetime.timedelta(days=i)
    D1.append( d )

fig, ax = plt.subplots()
ax.set_title( "Covid-19 USA Infection Rate", fontsize=20 )
ax.set_xlabel('Date', fontsize=14)
ax.ticklabel_format(axis="y",style="plain")
ax.set_ylabel( 'Number of Infections', fontsize=14 )
ax.set_yscale('log')
ax.plot( D, V, '--', color="blue", lw=2, label="Worst Case projection (from 3/7/2020)" )
ax.plot( D1, V1, '-', color="red", lw=2, label="Confirmed USA cases" )
ax.legend()
plt.show()
