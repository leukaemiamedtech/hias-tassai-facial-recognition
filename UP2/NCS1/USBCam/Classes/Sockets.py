######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 NCS1 Facial Recognition USB Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
# Contributors:
# Title:         Sockets Class
# Description:   Sockets helper functions.
# License:       MIT License
# Last Modified: 2020-09-28
#
######################################################################################################

import zmq

import numpy as np

from Classes.Helpers import Helpers

class Sockets():
	""" Sockets Class

	Sockets helper functions.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Helpers = Helpers("Sockets")

		self.Helpers.logger.info("Socket Helper Class initialization complete.")

	def connect(self, ip, port):
		""" Connects to the local Socket. """

		try:
			soc = zmq.Context().socket(zmq.PUB)
			soc.connect("tcp://"+ip+":"+str(port))
			self.Helpers.logger.info("Started & connected to socket server: tcp://"+ip+":"+str(port))
			return soc
		except:
			self.Helpers.logger.info(" Failed to connect to socket server: tcp://"+ip+":"+str(port))

	def subscribe(self, ip, port):
		""" Subscirbes to the server. """

		try:
			context = zmq.Context()
			rsoc = context.socket(zmq.SUB)
			rsoc.setsockopt(zmq.CONFLATE, 1)
			rsoc.bind("tcp://*:"+str(port))
			rsoc.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))
			self.Helpers.logger.info("Subscribed to socket: tcp://"+ip+":"+str(port))
			return rsoc
		except:
			self.Helpers.logger.info("Failed to connect to tcp://"+ip+":"+str(port))
