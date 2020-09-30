######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       UP2 NCS1 Realsense F200 Facial Recognition Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         NCS1 Class
# Description:   NCS1 helper functions.
# License:       MIT License
# Last Modified: 2020-09-29
#
######################################################################################################

import os, json, cv2, dlib, imutils

import numpy as np

from datetime import datetime
from imutils import face_utils
from mvnc import mvncapi as mvnc

from Classes.Helpers import Helpers


class NCS1():
	""" NCS1 Class

	NCS1 helper functions.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Known = []

		self.Helpers = Helpers("NCS1")

		self.Detector   = dlib.get_frontal_face_detector()
		self.Predictor = dlib.shape_predictor(
			self.Helpers.confs["Classifier"]["Dlib"])

		self.check()
		self.load()
		self.preprocess()

		self.Helpers.logger.info("NCS1 class initialized.")

	def check(self):
		""" Checks for NCS1 device. """

		#mvnc.SetGlobalOption(mvnc.GlobalOption.LOGLEVEL, 2)
		devices = mvnc.EnumerateDevices()

		if len(devices) == 0:
			self.Helpers.logger.info(
				"No Neural Compute Stick 1 devices, exiting")
			quit()

		self.ncs1 = mvnc.Device(devices[0])
		self.ncs1.OpenDevice()

		self.Helpers.logger.info("Connected to Neural Compute Stick 1")

	def load(self):
		""" Loads NCS1 graph. """

		with open(self.Helpers.confs["Classifier"]["Graph"], mode='rb') as f:
			graphFile = f.read()

		self.Helpers.logger.info("Loaded NCS1 graph")

		self.graph = self.ncs1.AllocateGraph(graphFile)

	def preprocess(self):
		""" Encodes the known users images. """

		self.encoded = []

		# Loops through all images in the security folder
		for filename in os.listdir(self.Helpers.confs["Classifier"]["Known"]):
			# Checks file type
			if filename.lower().endswith(tuple(self.Helpers.confs["Classifier"]["Allowed"])):
				fpath = os.path.join(
					self.Helpers.confs["Classifier"]["Known"], filename)
				# Gets user id from filename
				user = os.path.splitext(filename)[0]
				# Reads the image
				raw, frame = self.prepareImg(cv2.imread(fpath))
				# Saves the user id and encoded image to a list
				self.encoded.append((user, self.infer(frame)))

		self.Helpers.logger.info("Known data preprocessed!")

	def faces(self, image):
		""" Finds faces and their coordinates in an image. """

		# Find faces
		faces = self.Detector(image, 0)
		# Gets coordinates for faces
		coords = [self.Predictor(image, face) for face in faces]

		return faces, coords

	def bounding_box(self, rect):
		x = rect.left()
		y = rect.top()
		w = rect.right() - x
		h = rect.bottom() - y

		return (x, y, w, h)

	def prepareImg(self, frame):
		""" Reads & processes frame from the local TassAI. """

		# Resizes the frame
		frame = cv2.resize(frame, (640, 480))
		# Makes a copy of the frame
		raw = frame.copy()

		return raw, frame

	def processImg(self, img):
		""" Preprocesses an image for inference. """

		dims = 160
		resized = cv2.resize(img, (dims, dims))
		processed = self.whiten(resized)

		return processed

	def whiten(self, grayscaled):
		""" Creates a whitened image.  """

		mean = np.mean(grayscaled)
		std_dev = np.std(grayscaled)
		std_adjusted = np.maximum(std_dev, 1.0 / np.sqrt(grayscaled.size))
		whitened_image = np.multiply(np.subtract(grayscaled, mean), 1 / std_adjusted)

		return whitened_image

	def infer(self, img):
		""" Runs the image through NCS1. """

		self.graph.LoadTensor(self.processImg(img).astype(np.float16), None)
		output, userobj = self.graph.GetResult()

		return output

	def match(self, frame, coords):
		""" Checks faces for matches against known users. """

		msg = ""
		person = 0
		confidence = 0

		# Loops through known encodings
		for enc in self.encoded:
			# Encode current frame
			encoded = self.infer(frame)
			# Calculate if difference is less than or equal to
			recognize = self.compare(enc[1], encoded)
			# If known
			if recognize[0] == True:
				person = int(enc[0])
				confidence = recognize[1]
				msg = "TassAI identified User #" +  str(person)
				break

		if(person == 0):
			msg = "TassAI identified an intruder"

		self.Helpers.logger.info(msg)

		return person, confidence

	def compare(self, face1, face2):
		""" Determines whether two images are a match. """

		if (len(face1) != len(face2)):
			self.Helpers.logger.info("Distance Missmatch")
			return False

		tdiff = 0
		for index in range(0, len(face1)):
			diff = np.square(face1[index] - face2[index])
			tdiff += diff

		if (tdiff < 1.3):
			self.Helpers.logger.info("Calculated Match: " + str(tdiff))
			return True, tdiff
		else:
			self.Helpers.logger.info("Calculated Mismatch: " + str(tdiff))
			return False, tdiff
