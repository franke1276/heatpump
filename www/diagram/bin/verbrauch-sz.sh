#!/bin/bash
echo -e "Content-type: text/plain\r\n"
awk -f /home/pi/heatpump/www/diagram/bin/verbrauch-per-monat-sz.awk /var/lib/heatpumpMonitor/verbrauch.201*
