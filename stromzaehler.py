#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import struct
import sys
import time

class StromZaehler:
  HEADER_BYTE="\x1b"
 
  _ser = None

  def __init__(self, serialDevice="/dev/lesekopf0"):
    self._ser = serial.Serial(serialDevice, timeout=5, baudrate=9600)
    print "connection to StromZaehler via %s established" % (serialDevice)

  def getValue(self):
    headerCounter=0
    while 1:
      r = self._ser.read(1)
      print "%02x" % ord(r),
      if r == self.HEADER_BYTE:
        headerCounter += 1
      else:
        print " |"
        headerCounter = 0
  
      if headerCounter == 4:
        print "-header found"
        break
    byteCountToRead=10*16-4
    r = self._ser.read(byteCountToRead)
    if r[(byteCountToRead) - 7] != "\xff" or r[(byteCountToRead) - 6] != "\x56":
      raise BaseException, "Wrong position in protocol"
    
    value = r[(byteCountToRead) - 5:]
    for t in value:
      print "%02x" %ord(t),
    v = 0
    for i in range(0,5):
      v += ord(value[i]) * pow(256,(4-i))
    v = float(v) / 10000  
    return v

  def close(self):
    self._ser.close()


def main():
  sz = StromZaehler("/dev/lesekopf0")
  print "value: %f" % sz.getValue()

if __name__ == '__main__':
  main()
