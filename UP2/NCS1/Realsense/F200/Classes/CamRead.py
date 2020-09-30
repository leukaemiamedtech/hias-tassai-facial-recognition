######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 NCS1 Realsense F200 Facial Recognition Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         CamRead Class
# Description:   Reads frames from an F200 camera and streams them to a socket stream.
# License:       MIT License
# Last Modified: 2020-09-29
#
######################################################################################################

import base64
import cv2
import dlib
import os
import sys
import time

import numpy as np

from datetime import datetime
from imutils import face_utils
from threading import Thread

from Classes.Helpers import Helpers
from Classes.iotJumpWay import Device as iot
from Classes.TassAI import TassAI

import pyrealsense as pyrs
from pyrealsense.constants import rs_option

class CamRead(Thread):
	""" CamRead Class

	Reads frames from a Realsense F200 camera and streams them
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
		self.TassAI.ncs()

		# Starts the socket server
		soc = self.Sockets.connect(self.Helpers.confs["Socket"]["host"], self.Helpers.confs["Socket"]["port"])

		fps = ""
		framecount = 0
		count = 0
		time1 = 0
		time2 = 0

		self.publishes = [None] * (len(self.TassAI.NCS1.encoded) + 1)

		with pyrs.Service() as serv:
			with serv.Device() as dev:

				dev.apply_ivcam_preset(0)

				while True:
					t1 = time.perf_counter()

					dev.wait_for_frames()
					frame = dev.color
					frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

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

							# If iotJumpWay publish for user is in past
							if (self.publishes[int(known)] is None or (self.publishes[int(known)] + (1 * 20)) < time.time()):
								# Update publish time for user
								self.publishes[int(known)] = time.time()

								# Send iotJumpWay notification
								self.iot.channelPub("Sensors", {
									"Type": "TassAI",
									"Sensor": "F200 Camera",
									"Value": known,
									"Message": mesg
								})

								# Send iotJumpWay notification
								self.iot.channelPub("Cameras", {
									"Type": "TassAI",
									"Sensor": "F200 Camera",
									"Value": known,
									"Message": mesg
								})

							(x, y, w, h) = self.TassAI.NCS1.bounding_box(faces[i])
							cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

							cx = int(round(+(w/2)))
							cy = int(round(y+(h/2)))

							cv2.putText(frame, "User ID#"+str(known), (x, y - 5),
										cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)

							distance = dev.depth[cy][cx]/1000.0
							if(distance != 0.0):
								cv2.putText(frame, str(distance) + "cm", (x + (w - 20), y - 5),
										cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)


							# Draws facial landmarks
							for (x, y) in coordsi:
								cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
							# Adds user name to frame
							i += 1

					cv2.putText(frame, fps, (width-170, 30), cv2.FONT_HERSHEY_SIMPLEX,
								0.5, self.TassAI.color, 1, cv2.LINE_AA)

					d = dev.depth * dev.depth_scale * 1000
					d = cv2.applyColorMap(d.astype(np.uint8), cv2.COLORMAP_RAINBOW)

					cd = np.concatenate((frame, d), axis=1)

					# Streams the modified frame to the socket server
					encoded, buffer = cv2.imencode('.jpg', cd)
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
