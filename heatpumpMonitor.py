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

config = None

# Print usage message and exit
def usage(*args):
    sys.stdout = sys.stderr
    print __doc__
    print 50*"-"
    for msg in args: print msg
    sys.exit(2)

def logError(e):
    """ prints a string which a human readable error text """
    print "========= % s =========" % time.asctime()
    
    # args can be empty
    if e.args:
        if len(e.args) > 1:
            print str(e.args)
        else:
            print e.args[0]
    else:
        # print exception class name
        print str(e.__class__)
    print "---------"
    print traceback.format_exc()
    print "========="
    sys.stdout.flush()

def updateCCU(v):
	ccuUrl = "http://192.168.178.31:8080/api/set"
	requests.get(ccuUrl + "/AussenTemp/?value=" + str(v.get('outside_temp')))    
	requests.get(ccuUrl + "/KollectorTemp/?value=" + str(v.get('collector_temp')))    
    
def doMonitor():
    try:
        print "Starting ..."
        sys.stdout.flush()
        
        p = protocol.Protocol(config.getSerialDevice(), config.getProtocolVersionsDirectory(), config.getNewStyleSerialCommunication())
        s = storage.Storage(config.getDatabaseFile())
        j = json.Json(os.path.join(config.getRenderOutputPath(), "actual_values.json"))
        r = render.Render(config.getDatabaseFile(), config.getRenderOutputPath())
        c = None # ThreadedExec for copyCommand
        aReport = report.Report(config)
        t = thresholdMonitor.ThresholdMonitor(config, aReport)
        
        print "Up and running"
        sys.stdout.flush()
        
        counter = 0
        renderInterval = config.getRenderInterval()
        copyCommand = config.getCopyCommand()
        copyInterval = config.getCopyInterval()
        verbrauchsInterval = 60 * 24
        oldValue = {"compressor_heating": 0, "compressor_dhw": 0, "booster_dhw": 0, "booster_heating" : 0}
        sz_wp = stromzaehler.StromZaehler("/dev/lesekopfWP")
        sz_sz = stromzaehler.StromZaehler("/dev/lesekopfSZ")
        while 1:
            startTime = time.time()
            try:
                values = p.query()
                values["zaehlerstand_wp"] = sz_wp.getValueAsInt()
                values["zaehlerstand_sz"] = sz_sz.getValueAsInt()
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
            print "zaehlerstand_wp %f" % values["zaehlerstand_wp"]            
            print "zaehlerstand_sz %f" % values["zaehlerstand_sz"]            
            sys.stdout.flush()
            
            # render it if the time is right ... it takes a lot of cpu on small embedded systems
            if counter % renderInterval == 0:
                r.render()
            
            # upload it somewhere if it fits the time
            if copyCommand and counter % copyInterval == 0:
                if c and c.isAlive():
                    print "Error: External copy program still running, cannot start it again"
                    sys.stdout.flush()
                else:
                    c = threadedExec.ThreadedExec(copyCommand)
                    c.start()
            
            if counter % verbrauchsInterval == 0:
                timeString = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                
                print "{0} compressor_heating={1}, compressor_dhw={2}, booster_dhw={3}, booster_heating={4}".format(timeString, values["compressor_heating"] - oldValue["compressor_heating"], values["compressor_dhw"] - oldValue["compressor_dhw"], values["booster_heating"] - oldValue["booster_heating"], values["booster_dhw"] - oldValue["booster_dhw"])
                sys.stdout.flush()
                oldValue["compressor_heating"]=values["compressor_heating"]
                oldValue["compressor_dhw"]=values["compressor_dhw"]
                oldValue["booster_heating"]=values["booster_heating"]
                oldValue["booster_dhw"]=values["booster_dhw"]
            counter += 1
            
            # at last check the values if something needs to reported
            t.check(values)
            
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
