#!/usr/bin/env python
# -*- coding: utf-8 -*-

rrd_file = "/var/lib/stromverbrauch/strom.rrd"

zaehler = {
  "zaehlerstandWP" : {
    "color" : "#ff1100",
    "legend" : "Zaehlerstand Waermepumpe"
  },
  "zaehlerstandSZ" : {
    "color" : "#ff9900",
    "legend" : "Zaehlerstand Stromzaehler"
  }
}

from BaseHTTPServer import BaseHTTPRequestHandler
from pyrrd.rrd import DataSource, RRA, RRD
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, GPRINT
from pyrrd.graph import ColorAttributes
from pyrrd.graph import Graph
from urlparse import parse_qs
import urlparse
import time
import random
import os
import sys

hour = 60 * 60
day = 24 * hour
week = 7 * day
month = day * 30
quarter = month * 3
half = 365 * day / 2
year = 365 * day


def getIntOrElse(params, key, default):
  value = params.get(key)
  if value:
    return int(value[0])
  return default

def getBooleanOrElse(params, key, default):
  value = params.get(key)
  if value:
    return str(value[0]).lower() == "true"
  return default


class GetHandler(BaseHTTPRequestHandler):

  def _createLines(self):
    lines = []
    for zaehlerName, zaehlerData in zaehler.items():
      d = DEF(rrdfile=rrd_file, vname=zaehlerName, dsName=zaehlerName)
      line = LINE(value=zaehlerName, color=zaehlerData["color"], legend=zaehlerData["legend"])
      lines.extend([d, line])
    return lines

  def _render(self, params):
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

    currentTime = int(time.time())

    start = currentTime - getIntOrElse(params, "start", (3 * hour))
    end = currentTime - getIntOrElse(params, "end", 0)
    log = getBooleanOrElse(params, "log", False)
    step = getIntOrElse(params, "step", 60)
    width = getIntOrElse(params, "width", 800)
    height = getIntOrElse(params, "height", 400)

    generated_file = "/tmp/%d-%d.png" % (time.time(),random.randint(0, 100000))

    g = Graph(generated_file, start=start, end=end, vertical_label='100mWh/min', color=ca)
    g.data.extend(self._createLines())
    g.width = width
    g.height = height
    g.step = step
    g.logarithmic = log
    g.write()

    return generated_file

  def _handle_other(self, parsed_path):
    self.send_response(404)
    self.end_headers()

  def _handle_index(self, parsed_path):
    self.send_response(200)
    content = """<html>
      <head>
        <title>Stromverbrauch</title>
      </head>
      <body>
        <h1>Stromverbrauch</h1>
        <h2>3 Stunden</h2>
        <img src="graph?start=10800">
        <h2>12 Stunden</h2>
        <img src="graph?start=43200">
        <h2>24 Stunden</h2>
        <img src="graph?start=86400">
        <h2>7 Tage</h2>
        <img src="graph?start=604800&step=300">
      </body>
    </html>"""
    self.send_header("Content-Length", len(content))
    self.send_header("Content-Type", "text/html")

    self.end_headers()
    self.wfile.write(content)

  def _handle_graph(self, parsed_path):
    params = parse_qs(parsed_path.query)
    generated_graph_file = self._render(params)
    self.send_response(200)
    with open(generated_graph_file, 'r') as content_file:
      content = content_file.read()
      self.send_header("Content-Length", len(content))
      self.send_header("Content-Type", "image/png")

      self.end_headers()
      self.wfile.write(content)
    os.remove(generated_graph_file)

  def do_GET(self):
    parsed_path = urlparse.urlparse(self.path)

    if parsed_path.path == "/":
      self._handle_index(parsed_path)
    elif parsed_path.path == "/graph":
      self._handle_graph(parsed_path)
    else:
      self._handle_other(parsed_path)

    return

def main():
  port = 9000
  if len(sys.argv) > 1:
    port = int(sys.argv[1])
  from BaseHTTPServer import HTTPServer
  server = HTTPServer(('0.0.0.0', port), GetHandler)
  print "Starting server on port %d, use <Ctrl-C> to stop" % port
  server.serve_forever()

if __name__ == '__main__':
  main()