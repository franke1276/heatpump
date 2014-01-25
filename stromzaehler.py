#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import struct
import sys
import time

class StromZaehler:
  HEADER_BYTE1="\x1b"
  HEADER_BYTE2="\x01"
 
  _ser = None

  def __init__(self, serialDevice="/dev/lesekopf0"):
    self._ser = serial.Serial(serialDevice, timeout=5, baudrate=9600)
    print "connection to StromZaehler via %s established" % (serialDevice)


  def getValueAsInt(self):
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

  def close(self):
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
