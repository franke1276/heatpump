#!/usr/bin/env python
# -*- coding: utf-8 -*-

#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 3 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#***************************************************************************

"""
    This is the main module for the heatpump Monitor. It forks into the background
    and should to a polling every 60 secs. It is quit simple at this point, no
    config files or almost no error handling.

    Written by Robert Penz <robert@penz.name>
"""

#TODO: Create a common log system which is able to write a timestamp before the entry
#TODO: define which line is painted over which in the graphs

import time
import sys
import traceback
import os
import signal

import protocol
import storage
import json
import render
import deamon
import threadedExec
import config_manager
import report
import thresholdMonitor
import requests
import stromzaehler
import errorlog


config = None

# Print usage message and exit
def usage(*args):
    sys.stdout = sys.stderr
    print __doc__
    print 50*"-"
    for msg in args: print msg
    sys.exit(2)

def logError(e):
    errorlog.logError(e)

def updateCCU(v):
  ccuUrl = "http://pi:8080/api/set"
  try:
    requests.get(ccuUrl + "/AussenTemp/?value=" + str(v.get('outside_temp')))
    requests.get(ccuUrl + "/KollectorTemp/?value=" + str(v.get('collector_temp')))
  except Exception,e:
    logError(e)

def saveVerbrauchsData(v_wp,v_sz,zs_wp,zs_sz,interval):
  y = time.strftime('%Y', time.localtime())
  m = time.strftime('%m', time.localtime())
  d = time.strftime('%d', time.localtime())
  f = open("/var/lib/stromverbrauch/verbrauch.%s-%s-%s" %(y,m,d) , 'a')
  f.write("%s %04d %04d %d %d %d\n" % (time.strftime('%Y %m %d %a %H %H:%M:%S', time.localtime()), v_wp, v_sz, zs_wp,      zs_sz, interval))
  f.close


def doMonitor():
    try:
        print "Starting ..."
        sys.stdout.flush()

        p = protocol.Protocol(config.getSerialDevice(), config.getProtocolVersionsDirectory(), config.getNewStyleSerialCommunication())
        s = storage.Storage(config.getDatabaseFile())
        j = json.Json(os.path.join(config.getRenderOutputPath(), "actual_values.json"))
        aReport = report.Report(config)
        t = thresholdMonitor.ThresholdMonitor(config, aReport)

        print "Up and running"
        sys.stdout.flush()

        counter = 0
        sz_wp = stromzaehler.StromZaehler("/dev/lesekopfWP")
        sz_sz = stromzaehler.StromZaehler("/dev/lesekopfSZ")
        old_wp = sz_wp.getValueAsInt()
        old_sz = sz_sz.getValueAsInt()
        print "%d %d" % (old_wp, old_sz)
        sys.stdout.flush()
        time.sleep(60)
        while 1:
            startTime = time.time()
            try:
                zs_wp = sz_wp.getValueAsInt()
                zs_sz = sz_sz.getValueAsInt()
                v_wp = zs_wp - old_wp
                v_sz = zs_sz - old_sz
                old_wp = zs_wp
                old_sz = zs_sz
                print "%d %d %d %d " % (zs_wp, zs_sz, v_wp, v_sz)
                sys.stdout.flush()
                saveVerbrauchsData(v_wp, v_sz, zs_wp, zs_sz, 60)

                values = p.query()

                values["zaehlerstand_wp"] = v_wp
                values["zaehlerstand_sz"] = v_sz
            except Exception, e:
                # log the error and just try it again in 120 sec - sometimes the heatpump returns an error and works
                # seconds later again
                # If the query takes longer than 2 minutes, we get a negative value ... maybe a problem in rare contitions
                logError(e)
                t.gotQueryError()
                time.sleep(120 - (time.time() - startTime))
                continue

            # store the stuff

            s.add(values)
            updateCCU(values)
            # write the json file everything, as it does not use much cpu
            j.write(values)
            sys.stdout.flush()

            counter += 1

            # at last check the values if something needs to reported
            # t.check(values)

            # lets make sure it is aways 60 secs interval, no matter how long the last run took
            sleepTime = 61 - (time.time() - startTime)
            if sleepTime < 0:
                print "System is too slow for 60 sec interval by %d seconds" % abs(int(sleepTime))
            else:
                time.sleep(sleepTime)
    except Exception, e:
        # make sure the error got logged
        logError(e)

# Main program: parse command line and start processing
def main():
    global config
    config = config_manager.ConfigManager()
    deamon.startstop(config.getLogFile(), pidfile=config.getPidFile())
    doMonitor()

if __name__ == '__main__':
    main()
