#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


hour = 60 * 60
day = 24 * hour
week = 7 * day
month = day * 30
quarter = month * 3
half = 365 * day / 2
year = 365 * day


class GetHandler(BaseHTTPRequestHandler):


  def render(self, params):
    filename = "/var/lib/stromverbrauch/strom.rrd"
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

    currentTime = int(time.time())

    start =  currentTime - (3 * hour)


    if params.get("time"):
      start =  currentTime - int(params.get("time")[0])

    generated_file = "/tmp/%d-%d.png" % (time.time(),random.randint(0, 100000))
    g = Graph(generated_file, start=currentTime - 60 * 60 * 24 , end=currentTime, vertical_label='100mWh/min', color=ca)
    g.step = 60
    g.data.extend([def1, def2, line1, line2])
    g.width = 800
    g.height = 400
    g.start = start
    g.end = currentTime
    g.step  = 60
    g.write()
    return generated_file

  def do_GET(self):
    parsed_path = urlparse.urlparse(self.path)
    params = parse_qs(parsed_path.query)


    file = self.render(params)

    print file

    self.send_response(200)
    with open(file, 'r') as content_file:
      content = content_file.read()
      self.send_header("Content-Length", len(content))
      self.send_header("Content-Type", "image/png")

      self.end_headers()
      self.wfile.write(content)
    os.remove(file)
    return

if __name__ == '__main__':
  from BaseHTTPServer import HTTPServer
  server = HTTPServer(('0.0.0.0', 8000), GetHandler)
  print 'Starting server, use <Ctrl-C> to stop'
  server.serve_forever()