#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import struct
import sys
import time
import errorlog

class StromZaehler:
  HEADER_BYTE1="\x1b"
  HEADER_BYTE2="\x01"
  byteCountToRead=10*16-8

  _ser = None

  _serialDevice = None

  def __init__(self, serialDevice="/dev/lesekopf0"):
    self._serialDevice=serialDevice

  def _connect(self):
    self._ser = serial.Serial(self._serialDevice, timeout=5, baudrate=9600)

  def _readUntilHeader(self):
    headerCounter=0
    hb = self.HEADER_BYTE1
    while 1:
      r = self._ser.read(1)
      if r == hb:
        headerCounter += 1
      else:
        hb = self.HEADER_BYTE1
        headerCounter = 0

      if headerCounter == 4:
        hb = self.HEADER_BYTE2

      if headerCounter == 8:
        r = self._ser.read(self.byteCountToRead)
        if r[(self.byteCountToRead) - 7] == "\xff" and r[(self.byteCountToRead) - 6] == "\x56":
          return r


  def getValueAsInt(self):
    try:
      self._connect()
      r = self._readUntilHeader()
      value = r[(self.byteCountToRead) - 5:]
      v = 0
      for i in range(0,5):
        v += ord(value[i]) * pow(256,(4-i))
      self.close()
      return v
    except Exception, e:
      errorlog.logError(e)
      self.close()


  def close(self):
    self._ser.close()
    self._ser = None


def main():
  sz = StromZaehler("/dev/lesekopf0")
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()

if __name__ == '__main__':
  main()
