#!/bin/csh

#./clear.csh 7 means clear 7 days before files
if ("$1") then
    echo "clear $1 days before file"
    set days = $1
else
    echo "clear 7 days before file"
    set days = 7
endif

cd /ic/temp/ipdv/$USER/Crypto_ss/work
find . -maxdepth 1 -atime +$days | xargs rm -rf
cd -

