import time
import os
import stromzaehler
from pyrrd.rrd import DataSource, RRA, RRD
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, GPRINT
from pyrrd.graph import ColorAttributes

filename = '/tmp/test.rrd'
dataSources = []
roundRobinArchives = []
dataSource = DataSource(dsName='zaehlerstand', dsType='COUNTER', heartbeat=600)
dataSources.append(dataSource)
roundRobinArchives.append(RRA(cf='AVERAGE', xff=0, steps=1, rows=60/1 * 24))
startTime = int(time.time())

myRRD = RRD( filename, ds=dataSources, rra=roundRobinArchives, start=startTime, step=1)
myRRD.create()

print "start: %d "% startTime

time.sleep(1)

sz = stromzaehler.StromZaehler("/dev/lesekopf0")


c=10
while c > 0:
  v = sz.getValueAsInt()
  print "got value %d" % v
  myRRD.bufferValue(int(time.time()), str(v))
  myRRD.update()
  time.sleep(2)
  c -= 1


def1 = DEF(rrdfile=myRRD.filename, vname='myzaehlerstand', dsName=dataSource.name)
cdef1 = CDEF(vname='verbrauchpros', rpn='%s,86400,*' % def1.vname)
vdef1 = VDEF(vname='myavg', rpn='%s,AVERAGE' % def1.vname)

line = LINE(defObj=cdef1, color='#006600', legend='Zaehlerstand')
gprint1 = GPRINT(vdef1, '%6.2lf KWh per Day')

ca = ColorAttributes()
ca.back = '#333333'
ca.canvas = '#333333'
ca.shadea = '#000000'
ca.shadeb = '#111111'
ca.mgrid = '#CCCCCC'
ca.axis = '#FFFFFF'
ca.frame = '#AAAAAA'
ca.font = '#FFFFFF'
ca.arrow = '#FFFFFF'

from pyrrd.graph import Graph
graphfile = "/tmp/rrdgraph.png"
g = Graph(graphfile, start=startTime , end=startTime + 300, vertical_label='w/s', color=ca)
g.step = 10
g.data.extend([def1, cdef1, line, vdef1, gprint1])
g.width = 800
g.height = 400
g.write()
