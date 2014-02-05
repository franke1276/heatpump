#!/usr/bin/env python
# -*- coding: utf-8 -*-
from string import join

rrd_file = "/var/lib/heatpumpMonitor/heatpumpMonitor.rrd"

werte = {
  "zaehlerstand_wp" : {
    "color" : "#ff1100",
    "legend" : "Zaehlerstand Waermepumpe",
    "default" : True
  },
  "zaehlerstand_sz" : {
    "color" : "#ff9900",
    "legend" : "Zaehlerstand Stromzaehler",
    "default" : True
  },
  "flow_temp": {
    "color" : "#ffAA00",
    "legend" : "Vorlauftemperatur",
    "default" : True
  },
  "return_temp": {
    "color" : "#CC1100",
    "legend" : "Ruecklauftemperatur",
    "default" : True
  },
  "dhw_temp": {
    "color" : "#CC9900",
    "legend" : "Warmwassertemeratur",
    "default" : True
  },
  "outside_temp": {
    "color" : "#CCAA00",
    "legend" : "Aussentemperatur",
    "default" : True
  },
  "collector_temp": {
    "color" : "#991100",
    "legend" : "Kollektortemperatur",
    "default" : True
  },
  "heizung": {
    "color" : "#999900",
    "legend" : "Heizstufe",
    "default" : False
  },
  "evaporator_temp": {
    "color" : "#99AA00",
    "legend" : "Evaporatortemperatur",
    "default" : False
  },
  "condenser_temp": {
    "color" : "#661100",
    "legend" : "Kondensatortemperatur",
    "default" : False
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

def getStringOrElse(params, key, default):
  value = params.get(key)
  if value:
    return str(value[0])
  return default

def getBooleanOrElse(params, key, default):
  value = params.get(key)
  if value:
    return str(value[0]).lower() == "true"
  return default

def getAllZaehlerNames():
  z = []
  for zaehlerName, zaehlerData in werte.items():
    z.append(zaehlerName)
  return join(z, ",")

class GetHandler(BaseHTTPRequestHandler):


  def _createLines(self, graphs):
    lines = []
    for zaehlerName, zaehlerData in werte.items():
      for g in graphs.split(","):
        if zaehlerName == g:
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
    graphs = getStringOrElse(params, "graphs", getAllZaehlerNames())

    upperlimit = getIntOrElse(params, "upperlimit", None)
    lowerlimit = getIntOrElse(params, "lowerlimit", None)

    generated_file = "/tmp/%d-%d.png" % (time.time(),random.randint(0, 100000))

    g = Graph(generated_file, start=start, end=end, vertical_label='100mWh/min', color=ca)
    g.data.extend(self._createLines(graphs))
    g.width = width
    g.height = height
    g.step = step
    g.logarithmic = log

    if upperlimit:
      g.upper_limit=upperlimit
    if lowerlimit:
      g.lower_limit=lowerlimit

    g.rigid=True
    g.write()

    return generated_file

  def _handle_other(self, parsed_path):
    self.send_response(404)
    self.end_headers()

  def _handle_all(self, parsed_path):
    self.send_response(200)

    content ="""<html>
    <head>
      <title>Stromverbrauch</title>
    </head>
    <body>
      <h1>Stromverbrauch</h1>
      <a href="detail">detail</a>
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

  def _handle_detail(self, parsed_path):
    params = parse_qs(parsed_path.query)
    self.send_response(200)
    graphs = getStringOrElse(params,"graphs", getAllZaehlerNames())

    graphsParamStr = "&graphs=%s" % graphs

    checkBoxen = "<ul>"
    for zaehlerName, zaehlerData in werte.items():
      checked = ""
      if zaehlerData["default"]:
        checked="""checked="checked" """
      checkBoxen += """<li><input type="checkbox" class="wert" value="%s" %s> %s \n""" % (zaehlerName, checked, zaehlerData["legend"])

    checkBoxen += """<li><a href="javascript:alle();">alle</a>\n"""
    checkBoxen += """<li><a href="javascript:keine();">keine</a>\n"""
    checkBoxen += "</ul>"
    content = """
    <html>
  <head>
    <title>Stromverbrauch</title>
      <script src="http://code.jquery.com/jquery-2.1.0.min.js" ></script>

      <script type="text/javascript">
      function alle() {
        $(".wert").each(function(i){
          $(this).prop('checked', true)
        });
      }
      function keine() {
        $(".wert").each(function(i){
          $(this).prop('checked', false)
        });
      }

      function update() {
        var bild = $("#bild");
        var start = $("#start").val();
        var end = $("#end").val();
        var lowerlimit = $("#lowerlimit").val();
        var upperlimit = $("#upperlimit").val();
        var values = [];
        $(".wert").each(function(i){
          if ($(this).is(':checked')) {
            values.push($(this).attr("value"));
          }
        });

        bild.attr("src", "graph?start=" + (start * 3600) + "&end=" + (end * 3600) + "&graphs=" + values.join(",") + "&lowerlimit=" + lowerlimit + "&upperlimit=" + upperlimit);
        bild.fadeIn();

        $("#stundenlabel").html(start + " Stunden")
      }

$( document ).ready(function() {
    $("#gobutton").click(function(){
      update();
    });
    update();
});


    </script>
      </head>
      <body>
        <h1>Stromverbrauch</h1>
        <a href="/">Uebersicht</a>

        <div>
          Zeit (in h): <input type="text" id="start" value="6" size="3"> bis <input type="text" id="end" value="0" size="3"> (0 = jetzt)
          %s
          <p>Upper limit: <input type="text" id="upperlimit" value="100" size="3"></p>
          <p>Lower limit: <input type="text" id="lowerlimit" value="" size="3"></p>
          <input type="button" id="gobutton" value="&auml;ndern">
        </div>
        <h2 id="stundenlabel">24 Stunden</h2>
        <div id="imageContainter"></div>
        <img id="bild" src="">
      </body>
    </html>
    """ % (checkBoxen)
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
      self._handle_all(parsed_path)
    elif parsed_path.path == "/detail":
      self._handle_detail(parsed_path)
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
