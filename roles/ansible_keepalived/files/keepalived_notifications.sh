#!/bin/bash
# Copyright 2015, Jean-Philippe Evrard <jean-philippe@evrard.me>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

TYPE=$1
NAME=$2
NOW=`date "+%Y-%m-%d %H:%M:%S"`
NEWSTATE=$3
OLDSTATE=$(cat /var/run/keepalived.state)

echo "$NEWSTATE" > /var/run/keepalived.state

case $NEWSTATE in
        "FAULT") echo "$NOW Trying to restart haproxy to get out"\
                  "of faulty state" >> /var/log/keepalived-notifications.log
                 /etc/init.d/haproxy stop
                 /etc/init.d/haproxy start
                 exit 0
                 ;;
        *) echo "$NOW Unknown state" >> /var/log/keepalived-notifications.log
           exit 1
           ;;

esac
