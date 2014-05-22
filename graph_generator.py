#!/usr/bin/env python
# -*- coding: utf-8 -*-
from string import join
import deamon

rrd_file = "/var/lib/heatpumpMonitor/heatpumpMonitor.rrd"

werte = {
  "zaehlerstand_wp" : {
    "color" : "#ff1100",
    "legend" : "Verbrauch Waermepumpe",
    "default" : True
  },
  "zaehlerstand_sz" : {
    "color" : "#BBad4f",
    "legend" : "Verbrauch Stromzaehler",
    "default" : True
  },
  "flow_temp": {
    "color" : "#CC99DD",
    "legend" : "Vorlauftemperatur",
    "default" : True
  },
  "return_temp": {
    "color" : "#CC11FF",
    "legend" : "Ruecklauftemperatur",
    "default" : True
  },
  "dhw_temp": {
    "color" : "#F511CB",
    "legend" : "Warmwassertemeratur",
    "default" : True
  },
  "outside_temp": {
    "color" : "#F56C11",
    "legend" : "Aussentemperatur",
    "default" : True
  },
  "collector_temp": {
    "color" : "#F5AD11",
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
    logarithmic = getBooleanOrElse(params, "logarithmic", False)
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
    g.logarithmic = logarithmic

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

    content ="""<!DOCTYPE html>
    <html lang="en">
    <head>
      <title>Stromverbrauch</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
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




    checkBoxen = ""
    for zaehlerName, zaehlerData in werte.items():
      checked = ""
      if zaehlerData["default"]:
        checked="""checked="checked" """
      checkBoxen += """<div class="checkbox"><label><input type="checkbox" class="wert inputfield" value="%s" %s>%s</label></div>\n""" % (zaehlerName, checked, zaehlerData["legend"])
      #<input type="checkbox" class="wert inputfield" value="%s" %s> %s \n

    checkBoxen += """<a href="javascript:alle();">alle</a> <a href="javascript:keine();">keine</a>\n"""
    content = """
    <!DOCTYPE html>
    <html lang="en">
  <head>
      <title>Messwerte</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="http://code.jquery.com/jquery-2.1.0.min.js" ></script>
      <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.0/js/bootstrap.min.js" ></script>
      <link rel="stylesheet" type="text/css" href="//netdna.bootstrapcdn.com/bootstrap/3.1.0/css/bootstrap.min.css">


      <script type="text/javascript">
      function alle() {
        $(".wert").each(function(i){
          $(this).prop('checked', true)
        });
        update();
      }
      function keine() {
        $(".wert").each(function(i){
          $(this).prop('checked', false)
        });
        update();
      }

      function update() {
        var bild = $("#bild");
        var start = $("#start").val();
        var end = $("#end").val();
        var lowerlimit = $("#lowerlimit").val();
        var upperlimit = $("#upperlimit").val();
        var logarithmic = false;
          if ($("#logarithmic").is(':checked')) {
            logarithmic = true
          }
        var values = [];
        $(".wert").each(function(i){
          if ($(this).is(':checked')) {
            values.push($(this).attr("value"));
          }
        });

        bild.attr("src", "graph?start=" + (start * 3600) + "&end=" + (end * 3600) + "&graphs=" + values.join(",") + "&lowerlimit=" + lowerlimit + "&upperlimit=" + upperlimit + "&logarithmic=" + logarithmic);
        bild.fadeIn();

        $("#stundenlabel").html(start + " Stunden")
      }

$( document ).ready(function() {
    $(".inputfield").change(function(){
      update();
    });
    window.setInterval(update, 60000);
    update();
});


    </script>
      </head>
      <body>
        <div class="container">
          <div class="row">
            <div class="col-md-3">
              <h3>Parameter</h3>
              <h4>Zeiten</h4>
              <label class="sr-only" for="start">Start</label>
              <input type="text" class="form-control inputfield" id="start" placeholder="Start in h" size="3" value="4">

              <label class="sr-only" for="end">Ende</label>
              <input type="text" class="form-control inputfield" id="end" placeholder="Ende in h" size="3">

              <h4>Werte</h4>
              %s

              <h4>Limits</h4>
              <label class="sr-only" for="upperlimit">Upper limit</label>
              <input type="text" class="form-control inputfield" id="upperlimit" placeholder="Upper limit" size="3">

              <label class="sr-only" for="lowerlimit">Lower limit</label>
              <input type="text" class="form-control inputfield" id="lowerlimit" placeholder="Lower limit" size="3">

              <h4>Sonstiges</h4>
              <div class="checkbox"><label><input type="checkbox" class="inputfield" id="logarithmic">logarithmische Skala</label></div>
            </div>
            <div class="col-md-6">
              <h3 id="stundenlabel">24 Stunden</h3>
              <div id="imageContainter"></div>
              <img id="bild" src="">
            </div>
          </div>
        </div>
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
    sys.stdout.flush()
    return

def main():
  deamon.startstop("/var/log/stromverbrauch/graph_generator.log", pidfile="/var/run/graph_generator.pid")
  port = 9000
  from BaseHTTPServer import HTTPServer
  server = HTTPServer(('0.0.0.0', port), GetHandler)
  print "Starting server on port %d" % port
  sys.stdout.flush()
  server.serve_forever()

if __name__ == '__main__':
  main()
