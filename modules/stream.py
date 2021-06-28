#!/usr/bin/env python3
""" HIAS TassAI Video Stream.

Streams the processed frames to a local video server.

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

import cv2
import base64
import time
import zmq
import errno

import numpy as np

from PIL import Image
from io import BytesIO

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from threading import Thread

class stream(Thread):
	""" HIAS TassAI Stream

	Streams the processed frames to a local video server.
	"""

	def __init__(self, helpers):
		""" Initializes the class. """
		super(stream, self).__init__()

		self.helpers = helpers
		self.helpers.logger.info("Stream class initialized.")

	def run(self):
		""" Initializes the class. """

		global capture

		# Subscribes to the socket server
		capture = self.sockets.subscribe(
			self.helpers.credentials["server"]["ip"], self.helpers.credentials["server"]["socket"])

		try:
			server = ThreadedHTTPServer(
				(self.helpers.credentials["server"]["ip"], int(self.helpers.credentials["server"]["port"])), CamHandler)
			self.helpers.logger.info(
				"Camera server started on " + self.helpers.credentials["server"]["ip"]+":"+str(self.helpers.credentials["server"]["port"]))
			server.serve_forever()
		except KeyboardInterrupt:
			server.socket.close()
			capture.close()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			if self.path.endswith('.mjpg'):
					self.send_response(200)
					self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
					self.end_headers()
					count = 0

					while True:
						frame = capture.recv_string()
						frame = cv2.imdecode(np.fromstring(base64.b64decode(frame),
														dtype=np.uint8), 1)

						imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
						jpg = Image.fromarray(imgRGB)
						tmpFile = BytesIO()
						jpg.save(tmpFile,'JPEG')
						self.wfile.write("--jpgboundary".encode())
						self.send_header('Content-type','image/jpeg')
						self.send_header('Content-length',str(tmpFile.getbuffer().nbytes))
						self.end_headers()
						self.wfile.write(tmpFile.getvalue())
					return
		except IOError as e:
			print("Broken Pipe")
