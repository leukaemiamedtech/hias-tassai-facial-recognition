#!/bin/bash

PRN="HIAS TassAI Facial Recognition Agent"
PRURL="HIAS-TassAI-Facial-Recognition-Agent"
PRPYPATH="$PRURL/agent.py"
FMSG="- $PRN service installation terminated"

read -p "? This script will install the $PRN service on your device. Are you ready (y/n)? " cmsg

if [ "$cmsg" = "Y" -o "$cmsg" = "y" ]; then
	echo "- Installing $PRN service"
	sudo touch "/lib/systemd/system/$PRURL.service"
	echo "[Unit]" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "Description=$PRN service" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "After=multi-user.target" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "[Service]" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "User=$USER" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "Type=simple" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "Restart=on-failure" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "ExecStart=/usr/bin/python3 /home/$USER/$PRPYPATH" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "[Install]" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "WantedBy=multi-user.target" | sudo tee -a "/lib/systemd/system/$PRURL.service"
	echo "" | sudo tee -a "/lib/systemd/system/$PRURL.service"

	sudo systemctl enable $PRURL.service
	sudo systemctl start $PRURL.service

	echo "- Installed $PRN service!";
	exit 0
else
	echo $FMSG;
	exit 1
fi