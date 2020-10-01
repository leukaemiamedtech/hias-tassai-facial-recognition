######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Project:       OpenVINO USB Camera Security System
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         iotJumpWay Class
# Description:   iotJumpWay helper functions.
# License:       MIT License
# Last Modified: 2020-10-01
#
######################################################################################################

import os, json, sys, time

import paho.mqtt.client as mqtt

from Classes.Helpers import Helpers

class Device():
	""" iotJumpWay Class

	The iotJumpWay Class provides the EMAR device with  it's IoT functionality.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Helpers = Helpers("iotJumpWay")

		self.Helpers.logger.info("Initiating Local iotJumpWay Device.")

		self.mqttClient = None
		self.mqttTLS = "/etc/ssl/certs/DST_Root_CA_X3.pem"
		self.mqttHost = self.Helpers.confs["iotJumpWay"]['host']
		self.mqttPort = self.Helpers.confs["iotJumpWay"]['port']

		self.commandsCallback = None

		self.Helpers.logger.info("JumpWayMQTT Device Initiated.")

	def connect(self):

		self.Helpers.logger.info("Initiating Local iotJumpWay Device Connection.")

		self.mqttClient = mqtt.Client(client_id = self.Helpers.confs["iotJumpWay"]['dn'], clean_session = True)
		deviceStatusTopic = '%s/Device/%s/%s/Status' % (self.Helpers.confs["iotJumpWay"]['lid'], self.Helpers.confs["iotJumpWay"]['zid'], self.Helpers.confs["iotJumpWay"]['did'])
		self.mqttClient.will_set(deviceStatusTopic, "OFFLINE", 0, False)
		self.mqttClient.tls_set(self.mqttTLS, certfile=None, keyfile=None)
		self.mqttClient.on_connect = self.on_connect
		self.mqttClient.on_message = self.on_message
		self.mqttClient.on_publish = self.on_publish
		self.mqttClient.on_subscribe = self.on_subscribe
		self.mqttClient.username_pw_set(str(self.Helpers.confs["iotJumpWay"]['un']), str(self.Helpers.confs["iotJumpWay"]['pw']))
		self.mqttClient.connect(self.mqttHost, self.mqttPort, 10)
		self.mqttClient.loop_start()

		self.Helpers.logger.info("Local iotJumpWay Device Connection Initiated.")

	def on_connect(self, client, obj, flags, rc):

		self.Helpers.logger.info("Local iotJumpWay Device Connection Successful.")
		self.Helpers.logger.info("rc: " + str(rc))

		self.statusPub("ONLINE")

	def on_subscribe(self, client, obj, mid, granted_qos):

		self.Helpers.logger.info("JumpWayMQTT Subscription: "+str(mid))

	def on_message(self, client, obj, msg):

		print("JumpWayMQTT Message Received")
		splitTopic=msg.topic.split("/")

		if splitTopic[1]=='Devices':
			if splitTopic[4]=='Commands':
				if self.commandsCallback == None:
					print("** Device Commands Callback Required (commandsCallback)")
				else:
					self.commandsCallback(msg.topic, msg.payload)
			elif splitTopic[4]=='Triggers':
				if self.triggersCallback == None:
					print("** Device Notifications Callback Required (deviceNotificationsCallback)")
				else:
					self.triggersCallback(msg.topic, msg.payload)

	def statusPub(self, data):

		deviceStatusTopic = '%s/Devices/%s/%s/Status' % (self.Helpers.confs["iotJumpWay"]['lid'], self.Helpers.confs["iotJumpWay"]['zid'], self.Helpers.confs["iotJumpWay"]['did'])
		self.mqttClient.publish(deviceStatusTopic, data)
		self.Helpers.logger.info("Published to Device Status " + deviceStatusTopic)

	def channelPub(self, channel, data):

		deviceChannel = '%s/Devices/%s/%s/%s' % (self.Helpers.confs["iotJumpWay"]['lid'], self.Helpers.confs["iotJumpWay"]['zid'], self.Helpers.confs["iotJumpWay"]['did'], channel)
		self.mqttClient.publish(deviceChannel, json.dumps(data))

	def channelSub(self, channel, qos=0):

		if channel == None:
			self.Helpers.logger.info("** Channel (channel) is required!")
			return False
		else:
			deviceChannel = '%s/Devices/%s/%s/%s' % (self.Helpers.confs["iotJumpWay"]['lid'], self.Helpers.confs["iotJumpWay"]['zid'], self.Helpers.confs["iotJumpWay"]['did'], channel)
			self.mqttClient.subscribe(deviceChannel, qos=qos)
			self.Helpers.logger.info("-- Subscribed to Device "+channel+" Channel")

	def on_publish(self, client, obj, mid):

		self.Helpers.logger.info("-- Published to Device channel")

	def on_log(self, client, obj, level, string):

			print(string)

	def disconnect(self):
		self.statusPub("OFFLINE")
		self.mqttClient.disconnect()
		self.mqttClient.loop_stop()
