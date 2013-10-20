
import json
import os
import shutil
import threading
import time
import unittest

import paramiko
import fabric.api
from fabric.api import local, run, settings
import fabric.network

from SendorQueue import SendorTask, SendorAction

class FabricAction(SendorAction):

	def __init__(self, task):
		super(FabricAction, self).__init__(task)

	def fabric_local(self, command):
		with fabric.api.settings(warn_only=True):
			result = local(command, capture=True)
			self.task.append_details(command)
			self.task.append_details(result)
			self.task.append_details(result.stderr)
			if result.failed:
				raise Exception("Fabric command failed")
			return result

	def fabric_remote(self, command):
		with fabric.api.settings(warn_only=True):
			result = run(command)
			self.task.append_details(command)
			self.task.append_details(result)
			self.task.append_details(result.stderr)
			if result.failed:
				raise Exception("Fabric command failed")
			return result
				
class CopyFileAction(FabricAction):

	def __init__(self, task, source, target):
		super(CopyFileAction, self).__init__(task)
		self.source = source
		self.target = target

	def run(self):
		source = self.task.translate_path(self.source)
		target = self.task.translate_path(self.target)
		self.fabric_local('cp ' + source + ' ' + target)

	def string_description(self):
		return "Copy file " + self.source + " to " + self.target

class ScpSendFileAction(FabricAction):

	def __init__(self, task, source, filename, target):
		super(ScpSendFileAction, self).__init__(task)
		self.source = source
		self.filename = filename
		self.target = target

	def run(self):
		source_path = self.task.translate_path(self.source)
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

		source_path = self.task.translate_path(self.source)

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

class ParallelScpSendFileAction(FabricAction):

	def __init__(self, task, source, filename, target):
		super(ParallelScpSendFileAction, self).__init__(task)
		self.source = source
		self.filename = filename
		self.target = target
		self.transferred = None

	def run(self):

		source = self.task.translate_path(self.source)
		num_parallel_transfers = int(self.target['max_parallel_transfers'])
		temp_directory = self.task.work_directory
		temp_filename_prefix = 'chunk_'
		temp_file_prefix = os.path.join(temp_directory, temp_filename_prefix)

		self.fabric_local('split -d -n ' + str(num_parallel_transfers) + ' ' + source + ' ' + temp_file_prefix)
		
		def transfer_file_thread(self, tempfile, targetfile, target):
			source_path = tempfile
			target_path = self.target['user'] + '@' + self.target['host'] + ":" + targetfile
			target_port = self.target['port']
			key_file = self.target['private_key_file']
			self.fabric_local('scp ' + ' -B -P ' + target_port + ' -i ' + key_file + ' ' + source_path + ' ' + target_path)
				
		threads = []
			
		for i in range(num_parallel_transfers):
			temp_filename_suffix = u'%02d' % i
			tempfile = temp_file_prefix + temp_filename_suffix
			targetfile = temp_filename_prefix + temp_filename_suffix
			thread = threading.Thread(target=transfer_file_thread, args=(self, tempfile, targetfile, self.target))
			thread.start()
			threads.append(thread)

		for thread in threads:
			thread.join()

		host_string = self.target['user'] + '@' + self.target['host'] + ':' + self.target['port']
		with settings(host_string=host_string, key_filename=self.target['private_key_file']):
			print host_string
			self.fabric_remote('cat ' + temp_filename_prefix + '?? > ' + self.filename)
			self.fabric_remote('rm ' + temp_filename_prefix + '??')

	def string_description(self):
		if self.transferred:
			ratio = int(100 * self.transferred / self.total)
			return "Distribute to " + self.target['user'] + " - " + str(ratio) + "% sent"
		else:
			return "Distribute to " + self.target['user']

class ParallelSftpSendFileAction(FabricAction):

	def __init__(self, task, source, filename, target):
		super(ParallelSftpSendFileAction, self).__init__(task)
		self.source = source
		self.filename = filename
		self.target = target
		self.transferred = None

	def run(self):

		source = self.task.translate_path(self.source)
		num_parallel_transfers = int(self.target['max_parallel_transfers'])
		temp_directory = self.task.work_directory
		temp_filename_prefix = 'chunk_'
		temp_file_prefix = os.path.join(temp_directory, temp_filename_prefix)
		
		self.fabric_local('split -d -n ' + str(num_parallel_transfers) + ' ' + source + ' ' + temp_file_prefix)
		
		def transfer_file_thread(tempfile, targetfile, target):
			key_file = target['private_key_file']
			key = paramiko.RSAKey.from_private_key_file(key_file)
			transport = paramiko.Transport((target['host'], int(target['port'])))
			transport.connect(username = target['user'], pkey = key)
			sftp = paramiko.SFTPClient.from_transport(transport)
			sftp.put(tempfile, targetfile, callback=None)
				
		threads = []
			
		for i in range(num_parallel_transfers):
			temp_filename_suffix = u'%02d' % i
			tempfile = temp_file_prefix + temp_filename_suffix
			targetfile = temp_filename_prefix + temp_filename_suffix
			thread = threading.Thread(target=transfer_file_thread, args=(tempfile, targetfile, self.target))
			thread.start()
			threads.append(thread)

		for thread in threads:
			thread.join()

		host_string = self.target['user'] + '@' + self.target['host'] + ':' + self.target['port']
		with settings(host_string=host_string, key_filename=self.target['private_key_file']):
			print host_string
			self.fabric_remote('cat ' + temp_filename_prefix + '?? > ' + self.filename)
			self.fabric_remote('rm ' + temp_filename_prefix + '??')

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

		action = SftpSendFileAction(SendorTask(), self.source_path, self.file_name, target)
		action.run()

	def tearDown(self):
		shutil.rmtree(self.root_path)

class ParallelSftpSendFileActionUnitTest(unittest.TestCase):

	root_path = 'unittest'
	upload_root = root_path + '/upload'
	temp_path = root_path + '/temp'
	file_name = 'testfile'
	source_path = upload_root + '/' + file_name

	def setUp(self):
		os.mkdir(self.root_path)
		os.mkdir(self.upload_root)
		os.mkdir(self.temp_path)
		local('echo abc123 > ' + self.upload_root + '/' + self.file_name)

	def test_parallel_sftp_send_file_action(self):

		targets = {}
		with open('test/ssh_localhost_targets.json') as file:
			targets = json.load(file)

		target = targets['ssh_localhost_target3']

		task = SendorTask()
		task.set_queue_info(1, self.temp_path)
		action = ParallelSftpSendFileAction(task, self.source_path, self.file_name, target)
		action.run()

	def tearDown(self):
		shutil.rmtree(self.root_path)

if __name__ == '__main__':
	unittest.main()
	fabric.network.disconnect_all()
