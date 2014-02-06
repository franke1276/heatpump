#!/bin/bash

FILE=$1
TIME=$2
pgrep -f "heatpumpMonitor.py start" >> /dev/null 
if [ $? == 0 ]; then
  if [ `stat --format=%Y $FILE` -le $(( `date +%s` - $TIME )) ]; then 
    shutdown -r +2 
  fi
fi  
