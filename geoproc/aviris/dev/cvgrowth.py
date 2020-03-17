import matplotlib.pyplot as plt
import datetime

v = 3000
d = datetime.datetime.now()
dr = 3.0
npoints = 15

V = [v]
D = [ d ]
for i in range(0,npoints):
    v = v * 2
    V.append( v )
    d = d + datetime.timedelta(days=3)
    D.append( d )

fig, ax = plt.subplots()
ax.set_title( "Covid-19 USA Infection Rate", fontsize=20 )
ax.set_xlabel('Date', fontsize=14)
ax.ticklabel_format(axis="y",style="plain")
ax.set_ylabel( 'Number of Infections', fontsize=14 )
ax.semilogy( D, V, color="red", lw=2 )
plt.show()
