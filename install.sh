#!/bin/bash

cd /opt/wVote/

rm -rf __pycache__/

cp wvote.service /lib/systemd/system/wvote.service

date >> upgrade-log.txt
git rev-parse HEAD >> upgrade-log.txt

systemctl daemon-reload
systemctl start wvote.service
systemctl enable wvote.service
