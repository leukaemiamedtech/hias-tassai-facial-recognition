#!/usr/bin/env python3
""" HIAS TassAI Model.

Represents the HIAS TassAI Model. HIAS AI Models are used by AI Agents
to process incoming data.

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
import os
import os.path as osp

import numpy as np

from modules.OpenVINO.ie_module import InferenceContext
from modules.OpenVINO.landmarks_detector import LandmarksDetector
from modules.OpenVINO.face_detector import FaceDetector
from modules.OpenVINO.faces_database import FacesDatabase
from modules.OpenVINO.face_identifier import FaceIdentifier

from modules.camera import camera

from modules.AbstractModel import AbstractModel


class model(AbstractModel):
	""" HIAS TassAI Model.

	Represents the HIAS TassAI Model. HIAS AI Models
 	are used by AI Agents to process incoming data.
	"""

	def prepare_data(self):
		""" Creates/sorts dataset. """

		self.faces_database = FacesDatabase(os.path.dirname(os.path.abspath(__file__)) + '/../' + \
											self.helpers.confs["model"]["known"], self.face_identifier,
											self.landmarks_detector, self.face_detector, True)
		self.face_identifier.set_faces_database(self.faces_database)

		self.helpers.logger.info("Database is built, registered %s identities" %
								(len(self.faces_database)))

	def prepare_network(self):
		""" Prepares the network. """

		face_detector_net = self.load(
			os.path.dirname(os.path.abspath(__file__)) + '/../' + \
							self.helpers.confs["model"]["detection"])
		face_detector_net.reshape({"data": [1, 3, 384, 672]})

		landmarks_net = self.load(
			os.path.dirname(os.path.abspath(__file__)) + '/../' + \
							self.helpers.confs["model"]["landmarks"])

		face_reid_net = self.load(
			os.path.dirname(os.path.abspath(__file__)) + '/../' + \
							self.helpers.confs["model"]["reidentification"])

		self.face_detector = FaceDetector(face_detector_net,
										confidence_threshold=0.6,
										roi_scale_factor=1.15)

		self.landmarks_detector = LandmarksDetector(landmarks_net)

		self.face_identifier = FaceIdentifier(face_reid_net,
											match_threshold=0.3,
											match_algo='HUNGARIAN')

		self.face_detector.deploy(self.helpers.confs["model"]["runas"], self.context)
		self.landmarks_detector.deploy(self.helpers.confs["model"]["runas"], self.context,
										queue_size=self.qs)
		self.face_identifier.deploy(self.helpers.confs["model"]["runas"], self.context,
									queue_size=self.qs)

	def load(self, model_path):
		""" Loads a model from path. """

		self.qs = 16
		self.context = InferenceContext([
			self.helpers.confs["model"]["runas"], self.helpers.confs["model"]["runas"],
			self.helpers.confs["model"]["runas"]], "", "", "")

		model_path = osp.abspath(model_path)
		model_weights_path = osp.splitext(model_path)[0] + ".bin"

		self.helpers.logger.info("Loading the model from '%s'" % (model_path))
		model = self.context.ie_core.read_network(model_path, model_weights_path)
		self.helpers.logger.info("Model loaded")

		model_path = osp.abspath(model_path)
		model_weights_path = osp.splitext(model_path)[0] + ".bin"

		self.helpers.logger.info("Loading the model from '%s'" % (model_path))
		model = self.context.ie_core.read_network(model_path, model_weights_path)
		self.helpers.logger.info("Model loaded")

		return model

	def predict(self, frame):
		""" Gets a prediction for output features. """

		orig_image = frame.copy()
		frame = frame.transpose((2, 0, 1))
		frame = np.expand_dims(frame, axis=0)

		self.face_detector.clear()
		self.landmarks_detector.clear()
		self.face_identifier.clear()

		self.face_detector.start_async(frame)
		rois = self.face_detector.get_roi_proposals(frame)
		if self.qs < len(rois):
			self.helpers.logger.info("Too many faces for processing." \
					" Will be processed only %s of %s." % \
					(self.qs, len(rois)))
			rois = rois[:self.qs]
		self.landmarks_detector.start_async(frame, rois)
		landmarks = self.landmarks_detector.get_landmarks()

		self.face_identifier.start_async(frame, rois, landmarks)
		face_identities, unknowns = self.face_identifier.get_matches()

		outputs = [rois, landmarks, face_identities]

		return outputs

	def draw_text_with_background(self, frame, text, origin,
									font=cv2.FONT_HERSHEY_SIMPLEX, scale=1.0,
									color=(0, 0, 0), thickness=1, bgcolor=(255, 255, 255)):
		text_size, baseline = cv2.getTextSize(text, font, scale, thickness)
		cv2.rectangle(frame,
						tuple((origin + (0, baseline)).astype(int)),
						tuple((origin + (text_size[0], -text_size[1])).astype(int)),
						bgcolor, cv2.FILLED)
		cv2.putText(frame, text,
					tuple(origin.astype(int)),
					font, scale, color, thickness)
		return text_size, baseline

	def draw_detection_roi(self, frame, roi, identity):
		label = self.face_identifier.get_identity_label(identity.id)

		# Draw face ROI border
		cv2.rectangle(frame,
					tuple(roi.position), tuple(roi.position + roi.size),
					(0, 220, 0), 2)

		# Draw identity label
		text_scale = 0.5
		font = cv2.FONT_HERSHEY_SIMPLEX
		text_size = cv2.getTextSize("H1", font, text_scale, 1)
		line_height = np.array([0, text_size[0][1]])
		if label is "Unknown":
			text = label
		else:
			text = "User #" + label
		if identity.id != FaceIdentifier.UNKNOWN_ID:
			text += ' %.2f%%' % (100.0 * (1 - identity.distance))
		self.draw_text_with_background(frame, text,
									roi.position - line_height * 0.5,
									font, scale=text_scale)

		return frame, label

	def draw_detection_keypoints(self, frame, roi, landmarks):
		keypoints = [landmarks.left_eye,
				landmarks.right_eye,
				landmarks.nose_tip,
				landmarks.left_lip_corner,
				landmarks.right_lip_corner,
				landmarks.right_lip_corner]

		for point in keypoints:
				center = roi.position + roi.size * point
				cv2.circle(frame, tuple(center.astype(int)), 2, (0, 255, 255), 2)

		return frame

	def connect(self):
		""" Connects to the USB camera. """

		self.camera = camera(self.helpers)

		self.helpers.logger.info("Connected To Camera")

	def test(self):
		""" Test mode

		Loops through the test directory and classifies the images.
		"""

		totaltime = 0
		files = 0

		tp = 0
		fp = 0
		tn = 0
		fn = 0
		prediction = 0

		for testFile in os.listdir(self.testing_dir):
			if os.path.splitext(testFile)[1] in self.valid:

				fileName = self.testing_dir + "/" + testFile

				img = tf.keras.preprocessing.image.load_img(
					fileName, target_size=(224, 224), color_mode='rgb')
				out_fe = self.ext_feature(img)
				start = time.time()
				prediction = self.predict(out_fe)
				end = time.time()
				benchmark = end - start
				totaltime += benchmark

				msg = ""
				status = ""
				outcome = ""

				if prediction == 1 and "Non-Covid" in testFile:
					fp += 1
					status = "incorrectly"
					outcome = "(False Positive)"

				elif prediction == 0 and "Non-Covid" in testFile:
					tn += 1
					status = "correctly"
					outcome = "(True Negative)"

				elif prediction == 1 and "Covid" in testFile:
					tp += 1
					status = "correctly"
					outcome = "(True Positive)"

				elif prediction == 0 and "Covid" in testFile:
					fn += 1
					status = "incorrectly"
					outcome = "(False Negative)"

				files += 1
				self.helpers.logger.info("SARS-CoV-2 xDNN Classifier " + status +
								" detected " + outcome + " in " + str(benchmark) + " seconds.")

		self.helpers.logger.info("Images Classified: " + str(files))
		self.helpers.logger.info("True Positives: " + str(tp))
		self.helpers.logger.info("False Positives: " + str(fp))
		self.helpers.logger.info("True Negatives: " + str(tn))
		self.helpers.logger.info("False Negatives: " + str(fn))
		self.helpers.logger.info("Total Time Taken: " + str(totaltime))

	def test_http(self):
		""" HTTP test mode

		Loops through the test directory and classifies the images
		by sending data to the classifier using HTTP requests.
		"""

		totaltime = 0
		files = 0

		tp = 0
		fp = 0
		tn = 0
		fn = 0

		self.addr = "http://" + self.helpers.credentials["server"]["ip"] + \
			':'+str(self.helpers.credentials["server"]["port"]) + '/Inference'
		self.headers = {'content-type': 'image/jpeg'}

		for testFile in os.listdir(self.testing_dir):
			if os.path.splitext(testFile)[1] in self.valid:

				start = time.time()
				prediction = self.http_request(self.testing_dir + "/" + testFile)
				end = time.time()
				benchmark = end - start
				totaltime += benchmark

				msg = ""
				status = ""
				outcome = ""

				print()

				if prediction["Diagnosis"] == "Positive" and "Non-Covid" in testFile:
					fp += 1
					status = "incorrectly"
					outcome = "(False Positive)"

				elif prediction["Diagnosis"] == "Negative" and "Non-Covid" in testFile:
					tn += 1
					status = "correctly"
					outcome = "(True Negative)"

				elif prediction["Diagnosis"] == "Positive" and "Covid" in testFile:
					tp += 1
					status = "correctly"
					outcome = "(True Positive)"

				elif prediction["Diagnosis"] == "Negative" and "Covid" in testFile:
					fn += 1
					status = "incorrectly"
					outcome = "(False Negative)"

				files += 1
				self.helpers.logger.info("SARS-CoV-2 " + status +
								" detected " + outcome + " in " + str(benchmark) + " seconds.")

		self.helpers.logger.info("Images Classified: " + str(files))
		self.helpers.logger.info("True Positives: " + str(tp))
		self.helpers.logger.info("False Positives: " + str(fp))
		self.helpers.logger.info("True Negatives: " + str(tn))
		self.helpers.logger.info("False Negatives: " + str(fn))
		self.helpers.logger.info("Total Time Taken: " + str(totaltime))

	def ext_feature(self, img):
		"""  Extract feature from image """

		x = keras.preprocessing.image.img_to_array(img)
		x = np.expand_dims(x, axis=0)
		x = preprocess_input(x)
		features = self.tf_intermediate_layer_model.predict(x)
		test = []
		test.append(features[0])
		np_feature = np.array(test)

		return np_feature
