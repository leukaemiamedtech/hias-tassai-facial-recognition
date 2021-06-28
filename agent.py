#!/usr/bin/env python3
""" HIAS TassAI Facial Recognition Agent.

HIAS TassAI Facial Recognition Agent processes streams from local
or remote cameras to identify known and unknown humans.

MIT License

Copyright (c) 2021 Asociación de Investigacion en Inteligencia Artificial
Para la Leucemia Peter Moss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files(the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Contributors:
- Adam Milton-Barker

"""

import sys

from abc import ABC, abstractmethod

from modules.AbstractAgent import AbstractAgent

from modules.helpers import helpers
from modules.model import model
from modules.read import read
from modules.stream import stream
from modules.sockets import sockets

from threading import Thread


class agent(AbstractAgent):
	""" HIAS TassAI Facial Recognition Agent

	HIAS TassAI Facial Recognition Agent processes
 	streams from local or remote cameras to identify
	known and unknown humans.
	"""

	def set_model(self, mtype):

		# Inititializes the TassAI model
		self.model = model(self.helpers)

	def load_model(self):
		""" Loads the trained model """

		# Prepares the network and data
		self.model.prepare_network()
		self.model.prepare_data()

	def server(self):
		""" Loads the API server """

		# Starts the MQTT connection
		self.mqtt_start()
		# Inititializes the socket
		self.sockets = sockets(self.helpers)
		# Loads the TassAI model
		self.load_model()

		# Camera read and stream threads
		Thread(target=read.run, args=(self, ),
				daemon=True).start()
		Thread(target=stream.run, args=(self, ),
				daemon=True).start()

	def signal_handler(self, signal, frame):
		self.helpers.logger.info("Disconnecting")
		self.mqtt.disconnect()
		sys.exit(1)


agent = agent()


def main():

	if len(sys.argv) < 2:
		agent.helpers.logger.info(
			"You must provide an argument")
		exit()
	elif sys.argv[1] not in agent.helpers.confs["agent"]["params"]:
		agent.helpers.logger.info(
			"Mode not supported! server, train or inference")
		exit()

	mode = sys.argv[1]

	if mode == "classify":
		agent.set_model("")
		agent.inference()

	elif mode == "server":
		agent.set_model("")
		agent.server()


if __name__ == "__main__":
	main()
