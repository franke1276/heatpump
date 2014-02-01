#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import stromzaehler
from pyrrd.rrd import DataSource, RRA, RRD
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, GPRINT
from pyrrd.graph import ColorAttributes
import deamon
import threading
import signal
import sys

filename = '/var/lib/stromverbrauch/strom.rrd'

def saveVerbrauchsData(v_wp,v_sz,zs_wp,zs_sz,interval):
  y = time.strftime('%Y', time.localtime())
  m = time.strftime('%m', time.localtime())
  d = time.strftime('%d', time.localtime())
  f = open("/var/lib/stromverbrauch/verbrauch.%s-%s-%s" %(y,m,d) , 'a')
  f.write("%s %04d %04d %d %d %d\n" % (time.strftime('%Y %m %d %a %H %H:%M:%S', time.localtime()), v_wp, v_sz, zs_wp,   zs_sz, interval))
  f.close


def renderCharts(myRRD, startTime):
  print "start generating charts from %s ..." % filename
  def1 = DEF(rrdfile=filename, vname='zaehlerstandWP', dsName='zaehlerstandWP')
  def2 = DEF(rrdfile=filename, vname='zaehlerstandSZ', dsName='zaehlerstandSZ')

  line1 = LINE(value='zaehlerstandWP', color='#006600', legend='ZaehlerstandWP')
  line2 = LINE(value='zaehlerstandSZ', color='#ff6600', legend='ZaehlerstandSZ')

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
  graphfile = "/home/pi/heatpump/www/graphs/rrdgraph.png"
  currentTime = int(time.time())

  g = Graph(graphfile, start=currentTime - 60 * 60 * 24 , end=currentTime, vertical_label='KWh/min', color=ca)
  g.step = 60
  g.data.extend([def1, def2, line1, line2])
  g.width = 800
  g.height = 400
  g.write()
  g.logarithmic=True
  g.filename = "/home/pi/heatpump/www/graphs/rrdgraph-log.png"
  g.write()

  print "done generating charts."

def doMonitor():
  globalStartTime = int(time.time())
  print "start %d" % globalStartTime
  sys.stdout.flush()

  try:

    if os.path.isfile(filename):
      print "use existing rrd file %s" % filename
      myRRD = RRD(filename)
    else:
      print "create new rrd file %s" % filename
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

    timeSlot = 60
    sys.stdout.flush()
    time.sleep(timeSlot)
    counter = 0
    while 1:
      startTime = time.time()
      currentValueWP = sz.getValueAsInt()
      currentValueSZ = sz2.getValueAsInt()
      v = [currentValueWP - oldWP,  currentValueSZ - oldSZ]
      oldWP = currentValueWP
      oldSZ = currentValueSZ
      print "got verbrauch %d %d %d %d" % (v[0], v[1], currentValueWP, currentValueSZ)
      myRRD.bufferValue(int(time.time()), *v)
      saveVerbrauchsData(v[0], v[1], currentValueWP, currentValueSZ, timeSlot)

      myRRD.update()

      if counter % 2 == 0:
        renderCharts(myRRD, globalStartTime)

      counter += 1
      sleepTime = (timeSlot + 1) - (time.time() - startTime)
      sys.stdout.flush()
      if sleepTime < 0:
        print "System is too slow for 60 sec interval by %d seconds" % abs(int(sleepTime))
      else:
        time.sleep(sleepTime)
  except KeyboardInterrupt:
    print "Bye."

def main():
  deamon.startstop("/var/log/stromverbrauch/stromverbrauch.log", pidfile="/var/run/stromverbrauch/stromverbrauch.pid")
  doMonitor()

if __name__ == '__main__':
    main()
