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
 
  _ser = None

  _serialDevice = None

  def __init__(self, serialDevice="/dev/lesekopf0"):
    self._serialDevice=serialDevice

  def _connect(self):
    self._ser = serial.Serial(self._serialDevice, timeout=5, baudrate=9600)
    print "connection to StromZaehler via %s established" % (self._serialDevice)

  def getValueAsInt(self):
    if self._ser == None:
      self._connect()

    try:
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
          break
        
      byteCountToRead=10*16-8
      r = self._ser.read(byteCountToRead)
      if r[(byteCountToRead) - 7] != "\xff" or r[(byteCountToRead) - 6] != "\x56":
        print "buffer: ",
        for t in r: 
          print "%02x" % ord(t),
        raise BaseException, "Wrong position in protocol"
    
      value = r[(byteCountToRead) - 5:]
      v = 0
      for i in range(0,5):
        v += ord(value[i]) * pow(256,(4-i))
      return v
    except Exception, e:
      errorlog.logError(e)
      self._ser.close()
      self._ser = None


  def close(self):
    print "connection to %s closed" % self._serialDevice
    self._ser.close()


def main():
  sz = StromZaehler("/dev/lesekopf0")
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()
  print "value: %d" % sz.getValueAsInt()

if __name__ == '__main__':
  main()
