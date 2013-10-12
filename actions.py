
import json
import os
import shutil
import time
import unittest

import paramiko
import fabric.api
from fabric.api import local

from SendorQueue import SendorTask, SendorAction

class FabricAction(SendorAction):

	def __init__(self, task):
		super(FabricAction, self).__init__(task)
    
	def fabric_local(self, command):
		with fabric.api.settings(warn_only = True):
			result = local(command, capture = True)
			self.task.append_details(command)
			self.task.append_details(result)
			self.task.append_details(result.stderr)
			if result.failed:
				raise Exception("Fabric command failed")

class CopyFileAction(FabricAction):

	def __init__(self, task, source, target):
		super(CopyFileAction, self).__init__(task)
		self.source = source
		self.target = target

	def run(self):
		self.fabric_local('cp ' + self.source + ' ' + self.target)

	def string_description(self):
		return "Copy file " + self.source + " to " + self.target

class ScpSendFileAction(FabricAction):

	def __init__(self, task, source, filename, target):
		super(ScpSendFileAction, self).__init__(task)
		self.source = source
		self.filename = filename
		self.target = target

	def run(self):
		source_path = self.source
		target_path = self.target['user'] + '@' + self.target['host'] + ":" + self.filename
		target_port = self.target['port']
		key_file = self.target['private_key_file']
		self.fabric_local('scp ' + ' -B -P ' + target_port + ' -i ' + key_file + ' ' + source_path + ' ' + target_path)

	def string_description(self):
		return "Distribute to " + self.target['user']

class SftpSendFileAction(FabricAction):

	def __init__(self, task, source, filename, target):
		super(SftpSendFileAction, self).__init__(task)
		self.source = source
		self.filename = filename
		self.target = target
		self.transferred = None

	def run(self):

		def cb(transferred, total):
			self.transferred = transferred
			self.total = total

		source_path = self.source

		key_file = self.target['private_key_file']
		key = paramiko.RSAKey.from_private_key_file(key_file)
		transport = paramiko.Transport((self.target['host'], int(self.target['port'])))
		transport.connect(username = self.target['user'], pkey = key)
		sftp = paramiko.SFTPClient.from_transport(transport)
		sftp.put(source_path, self.filename, callback=cb)

	def string_description(self):
		if self.transferred:
			ratio = int(100 * self.transferred / self.total)
			return "Distribute to " + self.target['user'] + " - " + str(ratio) + "% sent"
		else:
			return "Distribute to " + self.target['user']


class CopyFileActionUnitTest(unittest.TestCase):

	def setUp(self):
		os.mkdir('unittest')
		local('echo abc123 > unittest/source')

	def test_copy_file_action(self):
		self.assertFalse(os.path.exists('unittest/target'))
		action = CopyFileAction(SendorTask(), 'unittest/source', 'unittest/target')
		action.run()
		self.assertTrue(os.path.exists('unittest/target'))

	def tearDown(self):
		shutil.rmtree('unittest')

class SftpSendFileActionUnitTest(unittest.TestCase):

	root_path = 'unittest'
	upload_root = root_path + '/upload'
	file_name = 'testfile'
	source_path = upload_root + '/' + file_name

	def setUp(self):
		os.mkdir(self.root_path)
		os.mkdir(self.upload_root)
		local('echo abc123 > ' + self.upload_root + '/' + self.file_name)

	def test_sftp_send_file_action(self):

		targets = {}
		with open('test/ssh_localhost_targets.json') as file:
			targets = json.load(file)

		target = targets['ssh_localhost_target2']

		task = SftpSendFileAction(SendorTask(), self.source_path, self.file_name, target)
		task.run()

	def tearDown(self):
		shutil.rmtree(self.root_path)

if __name__ == '__main__':
	unittest.main()
