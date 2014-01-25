#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import struct
import sys
import time

def printHex(s):
    print "debug: ",
    i = 0
    for t in s:
        #if i % 4 == 0:
            #print "| %d:" % i,
        print "%02x" % ord(t),
        i += 1
    print "|"
    sys.stdout.flush()


s = serial.Serial("/dev/lesekopf0", timeout=5, baudrate=9600)

b=""
HEADER_BYTE="\x1b"
headerCounter=0
while 1:
  r = s.read(1)
  if r == HEADER_BYTE:
    print "%02x" % ord(r),
    headerCounter += 1
  else:
    headerCounter = 0
  
  if headerCounter == 4:
    print "-header found"
    break
r = s.read(10 * 16 - 4)

for t in r:
  print "%02x" % ord(t),

value = r[(10 * 16 - 4) - 5:]

print "--"
for t in value:
  print "%02x" % ord(t)

v = 0
for i in range(0,5):
  print "(%d) + %d 256^%d = %d" % (i, ord(value[i]), 4-i, ord(value[i]) * (255^(4-i)))
  v += ord(value[i]) * pow(256,(4-i))

v = float(v) / 10000  
print "value: %f" % v

s.close()

