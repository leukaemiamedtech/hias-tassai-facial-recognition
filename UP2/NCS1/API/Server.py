######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 NCS1 Facial API Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         Server Class
# Description:   Hosts and API endpoint allowing facial recognition via HTTP requests.
# License:       MIT License
# Last Modified: 2020-09-28
#
######################################################################################################

import cv2
import jsonpickle
import geocoder
import json
import os
import psutil
import signal
import sys
import threading

import numpy as np

from imutils import face_utils

from Classes.Helpers import Helpers
from Classes.iotJumpWay import Device as iot
from Classes.NCS1 import NCS1

from flask import Flask, request, Response


class Server():
	""" Server Class

	Hosts and API endpoint allowing facial recognition via HTTP requests.
	"""

	def __init__(self):
		""" Initializes the Server class. """

		# Server setup
		self.Helpers = Helpers("Server")

		self.iotJumpWay()
		self.ncs()
		self.threading()

	def commands(self, topic, payload):
		"""
		iotJumpWay Commands Callback

		The callback function that is triggerend in the event of a
		command communication from the iotJumpWay.
		"""

		self.Helpers.logger.info(
			"Recieved iotJumpWay Command Data : " + payload.decode())
		command = json.loads(payload.decode("utf-8"))

	def iotJumpWay(self):

		# Starts the iotJumpWay
		self.iot = iot()
		self.iot.connect()

		# Subscribes to the commands topic
		self.iot.channelSub("Commands")

		# Sets the commands callback function
		self.iot.commandsCallback = self.commands

	def life(self):
		""" Sends vital statistics to HIAS """

		# Gets vitals
		cpu = psutil.cpu_percent()
		mem = psutil.virtual_memory()[2]
		hdd = psutil.disk_usage('/').percent
		tmp = psutil.sensors_temperatures()['coretemp'][0].current

		self.Helpers.logger.info(
			"TassAI Facial API Life (TEMPERATURE): " + str(tmp) + "\u00b0")
		self.Helpers.logger.info(
			"TassAI Facial API Life (CPU): " + str(cpu) + "%")
		self.Helpers.logger.info(
			"TassAI Facial API Life (Memory): " + str(mem) + "%")
		self.Helpers.logger.info(
			"TassAI Facial API Life (HDD): " + str(hdd) + "%")

		# Send iotJumpWay notification
		self.iot.channelPub("Life", {
			"CPU": cpu,
			"Memory": mem,
			"Diskspace": hdd,
			"Temperature": tmp,
			"Latitude": 41.5463,
			"Longitude": 2.1086
		})

		# Life thread
		threading.Timer(60.0, self.life).start()

	def ncs(self):
		""" Configures NCS1. """

		self.NCS1 = NCS1()

		self.known = self.Helpers.confs["Classifier"]["Known"]
		self.test = self.Helpers.confs["Classifier"]["Test"]

		self.Helpers.logger.info("NCS configured.")

	def threading(self):
		""" Starts the TassAI Facial API software threads. """

		# Life thread
		threading.Timer(60.0, self.life).start()

	def signal_handler(self, signal, frame):
		self.Helpers.logger.info("Disconnecting")
		self.iot.disconnect()
		sys.exit(1)


app = Flask(__name__)
Server = Server()


@app.route('/Encode', methods=['POST'])
def Encode():
	""" Responds to POST requests sent to the /Encode API endpoint. """

	return Server.NCS1.infer(Server.NCS1.prepareImg(np.fromstring(request.data, np.uint8)))


@app.route('/Inference', methods=['POST'])
def Inference():
	""" Responds to POST requests sent to the /Inference API endpoint. """

	detected = []
	resp = None
	idd = 0
	intruders = 0

	# Reads the image
	raw, frame = Server.NCS1.prepareImgRemote(
		np.fromstring(request.data, np.uint8))
	# Gets faces and coordinates
	faces, coords = Server.NCS1.faces(frame)

	if len(coords):
		i = 0
		msg = ""
		# Loops through coordinates
		for (i, face) in enumerate(coords):
			# Looks for matches/intruders
			known, distance = Server.NCS1.match(raw, faces[i])

			if known is not 0:
				idd += 1
				msg = "TassAI identified User #" + str(known)
			else:
				intruders += 1
				msg = "TassAI identified an intruder"

			detected.append((known, distance, msg))

			i += 1

		# Send iotJumpWay notification
		Server.iot.channelPub("Sensors", {
			"Type": "TassAI",
			"Sensor": "Facial API",
			"Value": detected,
			"Message": "GeniSys detected " + str(idd) +
                    " known humans and " + str(intruders) + " intruders."
		})

		resp = jsonpickle.encode({
			"Response": "OK",
			"Detections": detected
		})

		Server.Helpers.logger.info("GeniSys detected " + str(idd) +
                             " known humans and " + str(intruders) + " intruders.")

		return Response(response=resp, status=200, mimetype="application/json")

	else:

		Server.Helpers.logger.info(
			"GeniSys detected 0 known humans and 0 intruders.")

		resp = jsonpickle.encode({
			"Response": "FAILED",
			"Detections": []
		})

		return Response(response=resp, status=200, mimetype="application/json")


if __name__ == "__main__":
	signal.signal(signal.SIGINT, Server.signal_handler)
	signal.signal(signal.SIGTERM, Server.signal_handler)

	app.run(host=Server.Helpers.confs["Server"]["IP"],
			port=Server.Helpers.confs["Server"]["Port"])

	Server.NCS1.ncs1.DeallocateGraph()
	Server.NCS1.ncs1.CloseDevice()
