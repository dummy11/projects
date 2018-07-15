#!/bin/csh

if ("$1") then
    echo "clear $1 days before file"
    set days = $1
else
    echo "clear 7 days before file"
    set days = 7
endif

echo "00 0 * * 0 $PRJ_HOME/bin/clear.csh $days" > mycron
crontab mycron
rm mycron
