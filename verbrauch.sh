#!/bin/bash

FROM=$1
TO=$2

VALUE1=$(tail -1  /var/lib/heatpumpMonitor/verbrauch.$TO | awk '{print $9}' ) 
VALUE2=$(tail -1  /var/lib/heatpumpMonitor/verbrauch.$FROM | awk '{print $9}' )

echo "Verbrauch zwischen $FROM bis $TO: $(( ($VALUE1 - $VALUE2) / 10000 )) KW"
