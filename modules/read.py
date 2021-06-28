#!/usr/bin/env python3
""" HIAS TassAI Reader.

Receives the frames via the socket stream and processes them.
to identify known and unknown humans.

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

import base64, cv2, sys, time

from datetime import datetime
from imutils import face_utils
from threading import Thread

class read(Thread):
	""" HIAS TassAI Reader.

	Receives the frames via the socket stream and processes them.
	to identify known and unknown humans.
	"""

	def __init__(self, helpers, model):
		""" Initializes the class. """
		super(read, self).__init__()

		self.helpers = helpers
		self.model = model
		self.helpers.logger.info("HIAS TassAI Reader Class initialization complete.")

	def run(self):
		""" Runs the module. """

		fps = ""
		framecount = 0
		time1 = 0
		time2 = 0
		mesg = ""

		self.font = cv2.FONT_HERSHEY_SIMPLEX
		self.color = (0,0,0)

		# Connects to the camera
		self.model.connect()
		self.publishes = [None] * (len(self.model.faces_database) + 1)

		# Starts the socket server
		soc = self.sockets.connect(self.helpers.credentials["server"]["ip"],
									self.helpers.credentials["server"]["socket"])

		while True:
			try:
				t1 = time.perf_counter()

				# Reads the current frame
				frame = self.model.camera.get()

				width = frame.shape[1]
				# Processes the frame
				detections = self.model.predict(frame)

				# Writes header to frame
				cv2.putText(frame, "TassAI Stream", (10, 30), self.font,
							0.5, self.color, 1, cv2.LINE_AA)

				# Writes date to frame
				cv2.putText(frame, str(datetime.now()), (10, 50), self.font,
							0.3, self.color, 1, cv2.LINE_AA)

				if len(detections):
					for roi, landmarks, identity in zip(*detections):
						frame, label = self.model.draw_detection_roi(frame, roi, identity)
						#frame = self.model.draw_detection_keypoints(frame, roi, landmarks)

						if label is "Unknown":
							label = 0
							mesg = "TassAI identified intruder"
						else:
							mesg = "TassAI identified User #" + str(label)

						# If iotJumpWay publish for user is in past
						if (self.publishes[int(label)] is None or (self.publishes[int(label)] + (1 * 120)) < time.time()):
							# Update publish time for user
							self.publishes[int(label)] = time.time()

							# Send iotJumpWay notification
							self.mqtt.publish("Sensors", {
								"Sensor": "USB Camera",
								"Type": "classification",
								"Value": label,
								"Message": mesg
							})

							# Send iotJumpWay notification
							self.mqtt.publish("AI", {
								"Type": "classification",
								"Sensor": "USB Camera",
								"Value": label,
								"Message": mesg
							})

				cv2.putText(frame, fps, (width-120, 26), cv2.FONT_HERSHEY_SIMPLEX,
							0.3, self.color, 1, cv2.LINE_AA)

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
				self.model.lcv.release()
				break
