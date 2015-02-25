#! /bin/bash

sudo service ssh start
sudo cron -f &

./startup.sh
tail -f /dev/null