#!/bin/bash

HOST=$1

function check-1936 {
    if [[ "$(curl -k --head --silent --stderr /dev/null ${HOST}:1936/healthz)" =~ "200 OK" ]]; then
        return 0
    fi
    return 1
}

# Check to see if we already have a router and stats port ready to go
if check-1936; then 
    echo "OK"
    exit 0
fi

# No router running currently, setup netcat to test
echo "200 OK" | nc -l 1936 -w 5 &
if check-1936; then
   echo "OK"
   pkill -g 0 nc 2>&1 >/dev/null
   exit 0
else
# If we didn't connect to nc we need to kill it to cleanup
   pkill -g 0 nc 2>&1 >/dev/null
fi

exit 1

