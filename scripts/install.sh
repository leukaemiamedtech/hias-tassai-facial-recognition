#!/bin/bash

PRN="HIAS TassAI Facial Recognition Agent"
FMSG="- $PRN installation terminated"

read -p "? This script will install the $PRN on your device. Are you ready (y/n)? " proceed

if [ "$proceed" = "Y" -o "$proceed" = "y" ]; then
	echo "- Installing $PRN"

	sudo apt update
	sudo apt -y install cmake

	pip3 install --user scikit-build
	pip3 install --user opencv-python
	pip3 install --user dlib
	pip3 install --user geocoder
	pip3 install --user imutils
	pip3 install --user jsonpickle
	pip3 install --user paho-mqtt
	pip3 install --user psutil
	pip3 install --user zmq

	wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-detection-retail-0004/FP16/face-detection-retail-0004.bin -P model/
	wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-detection-retail-0004/FP16/face-detection-retail-0004.xml -P model/
	wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-reidentification-retail-0095/FP16/face-reidentification-retail-0095.bin -P model/
	wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-reidentification-retail-0095/FP16/face-reidentification-retail-0095.xml -P model/
	wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/landmarks-regression-retail-0009/FP16/landmarks-regression-retail-0009.bin -P model/
	wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/landmarks-regression-retail-0009/FP16/landmarks-regression-retail-0009.xml -P model/

	echo "- $PRN installed!"
else
	echo $FMSG;
	exit
fi