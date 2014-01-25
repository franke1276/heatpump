#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import struct
import sys
import time

def _calcChecksum(s):
    """ Internal function that calcuates the checksum """
    checksum = 1
    for i in xrange(0, len(s)):
        checksum += ord(s[i])
        checksum &= 0xFF
    return chr(checksum)

def addChecksum(s):
    """ inserts a the beginning a checksum """
    if len(s) < 1:
        raise ValueError, "The provided string needs to be atleast 1 byte long"
    return (_calcChecksum(s) + s)

def printData(t):
	print "Checksum: \t%02x\n" % ord(t[0]),
	print "Query: \t\t%02x\n" % ord(t[1]),
	print "Data: \t\t",
	for s in t[2:]:
		print "%02x " % ord(s),
	if t.find("\x01\xe5") != -1:
		print "FOUND."
	else:
		print "."
	sys.stdout.flush()

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

START="\x02"
BEGIN="\x01\x00"
ESCAPE="\x10"
END="\x03"
GETDATA="\x10"

def get(q):
  print "---- %02x ----" % ord(q)

  s.write(BEGIN + addChecksum(q) + ESCAPE + END)
  r = s.read(2)

  s.write(GETDATA)
  escaping=False
  b=""
  while 1:
	  r = s.read(1)
	  if escaping:
		  if r == END:
			  break
		  elif r == ESCAPE:
			  b += r
			  escaping = False
	  else:
		  if r == ESCAPE:
			  escaping = True
		  else:
			  b += r
		
  printData(b[2:])
  print "----------"
  s.write(ESCAPE + START)
  s.read(1)

s = serial.Serial("/dev/ttyUSB0", timeout=5, baudrate=115200)
s.write("\x02")
r = s.read(1)
for x in range(int(sys.argv[1]), 256):
  get(chr(x))

s.close()

