#!/bin/sh

echo "!! This program will setup everything you need to use OpenVINO USB Camera Security System !!"
echo " "

echo "-- Installing requirements"
echo " "

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
pip3 install --user tensorflow

wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-detection-retail-0004/FP16/face-detection-retail-0004.bin -P Model/
wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-detection-retail-0004/FP16/face-detection-retail-0004.xml -P Model/
wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-reidentification-retail-0095/FP16/face-reidentification-retail-0095.bin -P Model/
wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/face-reidentification-retail-0095/FP16/face-reidentification-retail-0095.xml -P Model/
wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/landmarks-regression-retail-0009/FP16/landmarks-regression-retail-0009.bin -P Model/
wget https://download.01.org/opencv/2020/openvinotoolkit/2020.3/open_model_zoo/models_bin/1/landmarks-regression-retail-0009/FP16/landmarks-regression-retail-0009.xml -P Model/