#!/usr/bin/env python3
""" USB Camera Class.

Connects to the USB camera and handles the frames.

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
import time

import multiprocessing as mp

class camera():
	""" USB Camera Class.

	Connects to the USB camera and handles the frames.
	"""

	def __init__(self, helpers):
		""" Initializes the class. """

		self.helpers = helpers

		self.parent, child = mp.Pipe()
		self.p = mp.Process(target=self.update, args=(child, self.helpers.confs["agent"]["cam"]))
		self.p.daemon = True
		self.p.start()

		self.helpers.logger.info("USB Camera Class initialized.")

	def end(self):
		""" Initializes the class. """

		self.parent.send(2)

	def update(self, conn, stream):
		""" Initializes the class. """

		self.helpers.logger.info("Connecting to USB camera.")
		cap = cv2.VideoCapture(stream)
		self.helpers.logger.info("Connected to USB camera.")
		run = True

		while run:
			cap.grab()
			rec_dat = conn.recv()

			if rec_dat == 1:
				ret,frame = cap.read()
				conn.send(frame)

			elif rec_dat ==2:
				cap.release()
				run = False

		conn.close()
		self.helpers.logger.info("USB camera connection closed.")

	def get(self,resize=None):
		""" Gets the frames. """

		self.parent.send(1)
		frame = self.parent.recv()
		self.parent.send(0)

		if resize == None:
			return frame
		else:
			return self.resize(frame, resize)

	def resize(self, frame, percent=65):

		return cv2.resize(frame,None,fx=percent,fy=percent)
