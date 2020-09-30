######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 NCS1 Realsense F200 Facial Recognition Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         CamStream Class
# Description:   Streams the processed frames to a local video server.
# License:       MIT License
# Last Modified: 2020-09-29
#
######################################################################################################

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

from Classes.Helpers import Helpers

class CamStream(Thread):
	""" CamStream Class

	Streams the processed frames to a local video server.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Helpers = Helpers("CamStream")
		super(CamStream, self).__init__()

		self.Helpers.logger.info("CamStream class initialized.")

	def run(self):
		""" Initializes the class. """

		global capture

		# Subscribes to the socket server
		capture = self.Sockets.subscribe(self.Helpers.confs["Socket"]["host"], self.Helpers.confs["Socket"]["port"])

		try:
			server = ThreadedHTTPServer(
				(self.Helpers.confs["Camera"]["IP"], self.Helpers.confs["Camera"]["Port"]), CamHandler)
			self.Helpers.logger.info(
				"Camera server started on " + self.Helpers.confs["Camera"]["IP"]+":"+str(self.Helpers.confs["Camera"]["Port"]))
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
