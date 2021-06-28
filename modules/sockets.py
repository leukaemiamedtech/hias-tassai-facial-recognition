#!/usr/bin/env python3
""" HIAS TassAI Socket Stream.

Socket stream for sending and receiving camera frames.

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

import zmq

import numpy as np

class sockets():
	""" HIAS TassAI Socket Stream

	Socket stream for sending photo frames to the server.
	"""

	def __init__(self, helpers):
		""" Initializes the class. """

		self.helpers = helpers

		self.helpers.logger.info("Socket Helper Class initialization complete.")

	def connect(self, ip, port):
		""" Connects to the local Socket. """

		try:
			soc = zmq.Context().socket(zmq.PUB)
			soc.connect("tcp://"+ip+":"+str(port))
			self.helpers.logger.info("Started & connected to socket server: tcp://"+ip+":"+str(port))
			return soc
		except:
			self.helpers.logger.info(" Failed to connect to socket server: tcp://"+ip+":"+str(port))

	def subscribe(self, ip, port):
		""" Subscirbes to the server. """

		try:
			context = zmq.Context()
			rsoc = context.socket(zmq.SUB)
			rsoc.setsockopt(zmq.CONFLATE, 1)
			rsoc.bind("tcp://*:"+str(port))
			rsoc.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))
			self.helpers.logger.info("Subscribed to socket: tcp://"+ip+":"+str(port))
			return rsoc
		except:
			self.helpers.logger.info("Failed to connect to tcp://"+ip+":"+str(port))
