#!/usr/bin/env python3
# ######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       OpenVINO USB Camera Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         Camera Class
# Description:   OpenVINO USB Camera Security System class.
# License:       MIT License
# Last Modified: 2020-10-01
#
######################################################################################################

import json
import psutil
import requests
import signal
import sys
import threading

from threading import Thread

from Classes.Helpers import Helpers
from Classes.iotJumpWay import Device as iot
from Classes.CamRead import CamRead
from Classes.CamStream import CamStream
from Classes.Sockets import Sockets

class Camera():
	""" Camera Class

	OpenVINO USB Camera Security System class.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Helpers = Helpers("Camera")

		# Initiates the iotJumpWay connection class
		self.iot = iot()
		self.iot.connect()
		# Subscribes to the commands topic
		self.iot.channelSub("Commands")
		# Sets the commands callback function
		self.iot.commandsCallback = self.commands

		self.Sockets = Sockets()

		self.Helpers.logger.info("Camera Class initialization complete.")

	def commands(self, topic, payload):
		"""
		iotJumpWay Commands Callback

		The callback function that is triggerend in the event of a
		command communication from the iotJumpWay.
		"""

		self.Helpers.logger.info(
			"Recieved iotJumpWay Command Data : " + payload.decode())
		command = json.loads(payload.decode("utf-8"))

	def life(self):
		""" Sends vital statistics to HIAS """

		cpu = psutil.cpu_percent()
		mem = psutil.virtual_memory()[2]
		hdd = psutil.disk_usage('/').percent
		tmp = psutil.sensors_temperatures()['coretemp'][0].current
		r = requests.get('http://ipinfo.io/json?token=15062dec38bfc3')
		data = r.json()
		location = data["loc"].split(',')

		self.Helpers.logger.info(
			"TassAI Life (TEMPERATURE): " + str(tmp) + "\u00b0")
		self.Helpers.logger.info("TassAI Life (CPU): " + str(cpu) + "%")
		self.Helpers.logger.info("TassAI Life (Memory): " + str(mem) + "%")
		self.Helpers.logger.info("TassAI Life (HDD): " + str(hdd) + "%")
		self.Helpers.logger.info("TassAI Life (LAT): " + str(location[0]))
		self.Helpers.logger.info("TassAI Life (LNG): " + str(location[1]))

		# Send iotJumpWay notification
		self.iot.channelPub("Life", {
			"CPU": cpu,
			"Memory": mem,
			"Diskspace": hdd,
			"Temperature": tmp,
			"Latitude": location[0],
			"Longitude": location[1]
		})

		threading.Timer(60.0, self.life).start()

	def threading(self):
		""" Creates required module threads. """

		# Life thread
		Thread(target=self.life, args=(), daemon=True).start()
		threading.Timer(60.0, self.life).start()

		# Camera read and stream
		Thread(target=CamRead.run, args=(self, ), daemon=True).start()
		Thread(target=CamStream.run, args=(self, ), daemon=True).start()

	def signal_handler(self, signal, frame):
		self.Helpers.logger.info("Disconnecting")
		self.iot.disconnect()
		sys.exit(1)

Camera = Camera()

def main():
	# Starts threading
	signal.signal(signal.SIGINT, Camera.signal_handler)
	signal.signal(signal.SIGTERM, Camera.signal_handler)
	Camera.threading()

if __name__ == "__main__":

	main()
