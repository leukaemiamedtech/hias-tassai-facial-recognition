######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 NCS1 Facial Recognition USB Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         CamRead Class
# Description:   Reads frames from a USB camera and streams them to a socket stream.
# License:       MIT License
# Last Modified: 2020-09-28
#
######################################################################################################

import base64
import cv2
import dlib
import os
import sys
import time

from datetime import datetime
from imutils import face_utils
from threading import Thread

from Classes.Helpers import Helpers
from Classes.iotJumpWay import Device as iot
from Classes.TassAI import TassAI

class CamRead(Thread):
	""" CamRead Class

	Reads frames from a USB camera and streams them
	to a socket stream.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Helpers = Helpers("CamRead")
		super(CamRead, self).__init__()

		self.Helpers.logger.info("CamRead class initialized.")

	def run(self):
		""" Runs the module. """

		self.identified = 0

		# Starts the TassAI module
		self.TassAI = TassAI()
		self.TassAI.cv()
		self.TassAI.connect()
		self.TassAI.ncs()

		# Starts the socket server
		soc = self.Sockets.connect(self.Helpers.confs["Socket"]["host"], self.Helpers.confs["Socket"]["port"])

		fps = ""
		framecount = 0
		count = 0
		time1 = 0
		time2 = 0

		while True:
			time.sleep(0.05)
			try:
				t1 = time.perf_counter()
				# Reads the current frame

				frame = self.TassAI.camera.get(0.65)

				# Processes the frame
				raw, frame = self.TassAI.NCS1.prepareImg(frame)
				width = frame.shape[1]

				# Gets faces and coordinates
				faces, coords = self.TassAI.NCS1.faces(frame)

				# Writes header to frame
				cv2.putText(frame, "TassAI", (10, 30), self.TassAI.font,
							0.7, self.TassAI.color, 2, cv2.LINE_AA)

				# Writes date to frame
				cv2.putText(frame, str(datetime.now()), (10, 50),
					self.TassAI.font, 0.5, self.TassAI.color, 2, cv2.LINE_AA)

				if len(coords):
					i = 0
					mesg = ""
					# Loops through coordinates
					for (i, face) in enumerate(coords):
						# Gets facial landmarks coordinates
						coordsi = face_utils.shape_to_np(face)
						# Looks for matches/intruders
						known, distance = self.TassAI.NCS1.match(raw, faces[i])

						if known:
							mesg = "TassAI identified User #" + str(known)
						else:
							mesg = "TassAI identified intruder"

						# Send iotJumpWay notification
						self.iot.channelPub("Sensors", {
							"Type": "TassAI",
							"Sensor": "Foscam Camera",
							"Value": known,
							"Message": mesg
						})

						# Draws facial landmarks
						for (x, y) in coordsi:
							cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
						# Adds user name to frame
						i += 1

				cv2.putText(frame, fps, (width-170, 30), cv2.FONT_HERSHEY_SIMPLEX,
									0.5, self.TassAI.color, 1, cv2.LINE_AA)

				# Streams the modified frame to the socket server
				encoded, buffer = cv2.imencode('.jpg', frame)
				soc.send(base64.b64encode(buffer))

				# FPS calculation
				framecount += 1
				if framecount >= 15:
					fps = "Stream: {:.1f} FPS".format(time1/15)
					framecount = 0
					time1 = 0
					time2 = 0
				t2 = time.perf_counter()
				elapsedTime = t2-t1
				time1 += 1/elapsedTime
				time2 += elapsedTime
				time.sleep(0.05)

			except KeyboardInterrupt:
				self.TassAI.camera.release()
				break
