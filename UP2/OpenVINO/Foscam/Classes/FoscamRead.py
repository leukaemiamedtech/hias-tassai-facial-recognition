#!/usr/bin/env python3
######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 OpenVINO Foscam Facial Recognition Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         FoscamRead Class
# Description:   Reads frames from a Foscam IP camera and streams them to a socket stream.
# License:       MIT License
# Last Modified: 2020-10-01
#
######################################################################################################

import base64
import cv2
import os
import sys
import time

from datetime import datetime
from imutils import face_utils
from threading import Thread

from Classes.Helpers import Helpers
from Classes.TassAI import TassAI

class FoscamRead(Thread):
	""" FoscamRead Class

	Reads frames from a Foscam IP camera and streams them
	to a socket stream.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Helpers = Helpers("FoscamRead")
		super(FoscamRead, self).__init__()

		self.Helpers.logger.info("FoscamRead class initialized.")

	def run(self):
		""" Runs the module. """

		fps = ""
		framecount = 0
		time1 = 0
		time2 = 0
		mesg = ""

		self.font = cv2.FONT_HERSHEY_SIMPLEX
		self.color = (0,0,0)

		# Starts the TassAI module
		self.TassAI = TassAI()
		# Connects to the camera
		self.TassAI.connect()
		# Loads the required models
		self.TassAI.load_models()
		# Loads known images
		self.TassAI.load_known()
		self.publishes = [None] * (len(self.TassAI.faces_database) + 1)

		# Starts the socket server
		soc = self.Sockets.connect(self.Helpers.confs["Socket"]["host"],
									self.Helpers.confs["Socket"]["port"])

		while True:
			try:
				t1 = time.perf_counter()

				# Reads the current frame
				frame = self.TassAI.camera.get(0.65)

				width = frame.shape[1]
				# Processes the frame
				detections = self.TassAI.process(frame)

				# Writes header to frame
				cv2.putText(frame, "TassAI Camera", (10, 30), self.font,
							0.7, self.color, 2, cv2.LINE_AA)

				# Writes date to frame
				cv2.putText(frame, str(datetime.now()), (10, 50), self.font,
							0.5, self.color, 2, cv2.LINE_AA)

				if len(detections):
					for roi, landmarks, identity in zip(*detections):
						frame, label = self.TassAI.draw_detection_roi(frame, roi, identity)
						#frame = self.TassAI.draw_detection_keypoints(frame, roi, landmarks)

						if label is "Unknown":
							label = 0
							mesg = "TassAI identified intruder"
						else:
							mesg = "TassAI identified User #" + str(label)

						# If iotJumpWay publish for user is in past
						if (self.publishes[int(label)] is None or (self.publishes[int(label)] + (1 * 20)) < time.time()):
							# Update publish time for user
							self.publishes[int(label)] = time.time()

							# Send iotJumpWay notification
							self.iot.channelPub("Sensors", {
								"Type": "TassAI",
								"Sensor": "Foscam Camera",
								"Value": label,
								"Message": mesg
							})

							# Send iotJumpWay notification
							self.iot.channelPub("Cameras", {
								"Type": "TassAI",
								"Sensor": "Foscam Camera",
								"Value": label,
								"Message": mesg
							})

				cv2.putText(frame, fps, (width-170, 26), cv2.FONT_HERSHEY_SIMPLEX,
							0.5, self.color, 1, cv2.LINE_AA)

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

			except KeyboardInterrupt:
				self.TassAI.lcv.release()
				break
