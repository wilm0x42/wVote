#!/bin/sh

excludes="--exclude=devAssets --exclude=weeks --exclude=__pycache__"


if [ -z "$1" ]; then
	echo "Usage: deploy.sh user@remotehost"
	exit 0
fi

echo "Uploading files via rsync"
rsync $excludes --delete -a . $1:/opt/wVote/
echo "Done!"

echo "Running install.sh on remote host"
ssh -t $1 -C "cd /opt/wVote/; sudo ./install.sh"
echo "Done!"