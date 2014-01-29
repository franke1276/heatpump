import time
import os
import stromzaehler
from pyrrd.rrd import DataSource, RRA, RRD
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, GPRINT
from pyrrd.graph import ColorAttributes

import threading
import signal
import sys

def renderCharts(myRRD, startTime):
  print "start generating charts ..."
  def1 = DEF(rrdfile=myRRD.filename, vname='myzaehlerstandWP', dsName='zaehlerstandWP')
  def2 = DEF(rrdfile=myRRD.filename, vname='myzaehlerstandSZ', dsName='zaehlerstandSZ')
  cdef1 = CDEF(vname='verbrauchWP', rpn='%s,60,*' % def1.vname)
  cdef2 = CDEF(vname='verbrauchSZ', rpn='%s,60,*' % def2.vname)
  vdef1 = VDEF(vname='myavgWP', rpn='%s,AVERAGE' % def1.vname)
  vdef2 = VDEF(vname='myavgSZ', rpn='%s,AVERAGE' % def2.vname)

  line1 = LINE(defObj=cdef1, color='#006600', legend='ZaehlerstandWP')
  line2 = LINE(defObj=cdef2, color='#ff6600', legend='ZaehlerstandSZ')

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
  graphfile = "www/graphs/rrdgraph.png"
  currentTime = int(time.time())

  g = Graph(graphfile, start=currentTime - 60 * 60 * 4 , end=currentTime, vertical_label='KWh/min', color=ca)
  g.step = 60
  g.data.extend([def1, def2, cdef1, cdef2, line1, line2, vdef1, vdef2])
  g.width = 800
  g.height = 400
  g.write()
  g.logarithmic=True
  g.filename = "www/graphs/rrdgraph-log.png"
  g.write()

  print "done generating charts."

def main():
  globalStartTime = int(time.time())
  print "start %d" % globalStartTime
  
  try:
    filename = '/tmp/test.rrd'

    if os.path.isfile(filename):
      print "use existing rrd file"
      myRRD = RRD(filename)
    else:
      print "create new rrd file"
      dataSources = []
      roundRobinArchives = []
      ds1 = DataSource(dsName='zaehlerstandWP', dsType='GAUGE', heartbeat=600)
      ds2 = DataSource(dsName='zaehlerstandSZ', dsType='GAUGE', heartbeat=600)

      dataSources.append(ds1)
      dataSources.append(ds2)
      roundRobinArchives.append(RRA(cf='AVERAGE', xff=0, steps=1, rows=60/1 * 24))
      myRRD = RRD( filename, ds=dataSources, rra=roundRobinArchives, start=globalStartTime, step=1)
      myRRD.create()

    time.sleep(1)
    sz = stromzaehler.StromZaehler("/dev/lesekopfWP")
    sz2 = stromzaehler.StromZaehler("/dev/lesekopfSZ")

    oldWP = sz.getValueAsInt()
    oldSZ = sz2.getValueAsInt()
    time.sleep(60) 
    counter = 0
    while 1:
      startTime = time.time()
      currentValueWP = sz.getValueAsInt()
      currentValueSZ = sz2.getValueAsInt()
      v = [currentValueWP - oldWP,  currentValueSZ - oldSZ]
      oldWP = currentValueWP
      oldSZ = currentValueSZ
      print "got verbrauch %d %d" % (v[0], v[1])
      myRRD.bufferValue(int(time.time()), *v)

      myRRD.update()  

      if counter % 2 == 0:
        renderCharts(myRRD, globalStartTime)

      counter += 1  
      sleepTime = 61 - (time.time() - startTime)
      if sleepTime < 0:
        print "System is too slow for 60 sec interval by %d seconds" % abs(int(sleepTime))
      else:
        time.sleep(sleepTime)
  except KeyboardInterrupt:
    sz.close()
    sz2.close()
    print "Bye."

if __name__ == '__main__':
    main()