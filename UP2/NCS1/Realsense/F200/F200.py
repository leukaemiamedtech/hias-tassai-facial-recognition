#!/usr/bin/env python3
######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 NCS1 Realsense F200 Facial Recognition Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         F200 Class
# Description:   UP2 NCS1 Realsense F200 Facial Recognition Security System class.
# License:       MIT License
# Last Modified: 2020-09-29
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


class F200():
	""" F200 Class

	UP2 NCS1 Realsense F200 Facial Recognition Security System class.
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

		self.Helpers.logger.info("F200 Class initialization complete.")

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
		r = requests.get('http://ipinfo.io/json?token=' +
                   self.Helpers.confs["iotJumpWay"]["ipinfo"])
		data = r.json()
		location = data["loc"].split(',')

		self.Helpers.logger.info("TassAI Life (TEMPERATURE): " + str(tmp) + "\u00b0")
		self.Helpers.logger.info("TassAI Life (CPU): " + str(cpu) + "%")
		self.Helpers.logger.info("TassAI Life (Memory): " + str(mem) + "%")
		self.Helpers.logger.info("TassAI Life (HDD): " + str(hdd) + "%")
		self.Helpers.logger.info("TassAI Life (LAT): " + str(location[0]))
		self.Helpers.logger.info("TassAI Life (LNG): " + str(location[1]))

		# Send iotJumpWay notification
		self.iot.channelPub("Life", {
			"CPU": str(cpu),
			"Memory": str(mem),
			"Diskspace": str(hdd),
			"Temperature": str(tmp),
			"Latitude": float(location[0]),
			"Longitude": float(location[1])
		})

		threading.Timer(300.0, self.life).start()

	def threading(self):
		""" Creates required module threads. """

		# Life thread
		threading.Timer(300.0, self.life).start()

		# Camera read and stream
		Thread(target=CamRead.run, args=(self, ), daemon=True).start()
		Thread(target=CamStream.run, args=(self,), daemon=True).start()

	def signal_handler(self, signal, frame):
		self.Helpers.logger.info("Disconnecting")
		self.iot.disconnect()
		sys.exit(1)


F200 = F200()


def main():
	# Starts threading
	signal.signal(signal.SIGINT, F200.signal_handler)
	signal.signal(signal.SIGTERM, F200.signal_handler)
	F200.threading()


if __name__ == "__main__":
	main()
