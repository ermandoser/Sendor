
import datetime
import json
import os
import os.path
import shutil
import unittest

from fabric.api import local

class StashedFile(object):

	def __init__(self, id, root_path, filename, sha1sum, timestamp, size):
		self.id = id
		self.root_path = root_path
		self.full_path_filename = os.path.join(root_path, sha1sum)
		self.original_filename = filename
		self.sha1sum = sha1sum
		self.timestamp = timestamp
		self.size = size

		if len(sha1sum) != 40:
			raise Exception(sha1sum + " is not a valid SHA1 hash value")
			
	def to_json(self):
		return { 'original_filename' : self.original_filename,
			'sha1sum' : self.sha1sum,
			'timestamp' : str(self.timestamp),
			'size' : str(self.size) }

class FileStash(object):

	index_filename = 'index.json'

	def __init__(self, root_path):
		if not os.path.exists(root_path):
			raise Exception("Stash directory " + root_path + " does not exist")
		self.root_path = root_path
		self.build_index()

	def save_index(self):
		filename = os.path.join(self.root_path, self.index_filename)
		with open(filename, 'w') as index_file:
			json.dump(self.files, index_file, default = lambda file: file.to_json())
			
	def build_index(self):
		""" Create an index for all the files in the stash directory tree """

		# Locate all on-disk files in file stash directory; remove directories
		old_files = {}
		for root, dirs, filenames in os.walk(self.root_path):

			for dir in dirs:
				shutil.rmtree(os.path.join(root, dir))
		
			for filename in filenames:
				if filename != self.index_filename:
					old_files[filename] = True;

		# Load index file
		old_index_filename = os.path.join(self.root_path, self.index_filename)
		old_index = {}
		try:
			with open(old_index_filename) as old_index_file:
				old_index = json.load(old_index_file)
		except IOError as e:
			pass

		# Remove index entries if the corresponding file is missing on-disk
		for id, entry in old_index.items():
			if not entry['sha1sum'] in old_files:
				del old_index[id]

		# Remove files which are not referenced by any index entry
		referenced_files = {}
		for entry in old_index.values():
			referenced_files[entry['sha1sum']] = True
			
		for file in old_files.keys():
			if not file in referenced_files:
				os.remove(os.path.join(self.root_path, file))
				
		# Add all remaining index entries to stash
		self.unique_id = 0
		self.files = {}
		for file in old_index.values():
			self.add_to_index(file['original_filename'], file['sha1sum'], file['timestamp'], file['size'])
			
		self.save_index()

	def add_to_index(self, filename, sha1sum, timestamp, size):
		""" Add a new file to the index
			The file should be present in the stash directory tree
			"""
		file = StashedFile(str(self.unique_id), self.root_path, filename, sha1sum, timestamp, size)
		self.files[str(self.unique_id)] = file
		self.unique_id = self.unique_id + 1
		return file

	def remove_from_index(self, id):
		""" Remove a file from the index
			The file will not be removed from the stash directory tree
			"""
		del self.files[id]

	def get(self, id):
		""" Locate the index entry for a file, or return None if it does not exist """
		return self.files.get(id)

	def add(self, original_path, filename, timestamp):
		""" Add a file to the stash
			If the file does not yet exist in the stash directory tree, the file will be moved
			from its original location to the stash
			Otherwise, the file is simply deleted from its original location
			"""
		original_file = os.path.join(original_path, filename)

		sha1sum = local('sha1sum -b ' + original_file, capture = True)[:40]
		size = os.stat(original_file).st_size

		file = self.add_to_index(filename, sha1sum, timestamp, size)

		if os.path.exists(file.full_path_filename):
			os.remove(original_file)
		else:
			shutil.move(original_file, file.full_path_filename)

		self.save_index()
		return file

	def remove(self, id):
		""" Remove a file from the stash
			The file should exist in the index and stash directory tree
			If this is the last reference to the on-disk file, the on-disk file will be removed
			"""

		file = self.get(id)
		sha1sum = file.sha1sum
		full_path_filename = file.full_path_filename
		self.remove_from_index(id)

		found = False
		for file in self.files.values():
			if file.sha1sum == sha1sum:
				found = True
				
		if not found:
			os.remove(full_path_filename)

		self.save_index()

	def nuke(self):
		""" Erase all files from stash """
		shutil.rmtree(self.root_path)
		os.mkdir(self.root_path)
		self.build_index()
		
class StashedFileUnitTest(unittest.TestCase):

	def test_file(self):

		self.assertRaises(Exception, StashedFile, 1, "root/path", "myfilename", "invalid_hash")

		file = StashedFile(1, "root/path", "myfilename", "cf53e64d1bb75ce5a4e71324777d7ed6cc19c435", datetime.datetime.utcnow(), 1234)
		self.assertEquals(file.full_path_filename, "root/path/cf53e64d1bb75ce5a4e71324777d7ed6cc19c435")

class FileStashUnitTest(unittest.TestCase):

	file1_name = 'hello1.txt'
	file1_sha1sum = 'a2abbbf0d432a8097fd7a4d421cc91881309cda2'
	file2_name = 'hello2.txt'
	file2_sha1sum = 'dca028d53b41169f839eeefe489b02e0aa7b5d27'
	file3_name = 'hello3.txt'
	file3_sha1sum = 'ca44a076d1ac49f10ebb55949a9a16805af69bcd'
	file4_name = 'hello1.txt'
	file4_sha1sum = '77b8b233f03f1720c0642f6e1ce395fbfe0322ed'
	file5_name = 'hello5.txt'
	file5_sha1sum = 'ca44a076d1ac49f10ebb55949a9a16805af69bcd'

	def setUp(self):

		# Construct a file-stash
		os.mkdir('unittest')
		os.mkdir('unittest/file_stash')

	def test(self):

		# Add two files to the stash
		file_stash_init = FileStash('unittest/file_stash')
		local('echo "Hello World 1" > unittest/' + self.file1_name)
		local('echo "Hello World 2" > unittest/' + self.file2_name)
		file_stash_init.add('unittest', self.file1_name, datetime.datetime.utcnow())
		file_stash_init.add('unittest', self.file2_name, datetime.datetime.utcnow())

		# Create three temporary files outside of the stash
		local('echo "Hello World 3" > unittest/' + self.file3_name)
		local('echo "Hello World 4" > unittest/' + self.file4_name)
		local('echo "Hello World 3" > unittest/' + self.file5_name)

		file_stash = FileStash('unittest/file_stash')
		# file1 and file2 should already exist in the file stash
		self.assertEquals(len(file_stash.files), 2)

		# Files not in the stash should not yield any hits
		self.assertEquals(file_stash.get(12345678), None)

		# file4 has the same filename as file1
		# file3 and file5 have different names but identical content

		file3 = file_stash.add('unittest', self.file3_name, datetime.datetime.utcnow())
		file4 = file_stash.add('unittest', self.file4_name, datetime.datetime.utcnow())
		file5 = file_stash.add('unittest', self.file5_name, datetime.datetime.utcnow())

		file3_id = file3.id
		file4_id = file4.id
		file5_id = file5.id

		# Validate that all files have been added to the stash
#		self.assertNotEquals(file_stash.get(self.file1_name, self.file1_sha1sum), None)
#		self.assertNotEquals(file_stash.get(self.file2_name, self.file2_sha1sum), None)
		self.assertNotEquals(file_stash.get(file3_id), None)
		self.assertNotEquals(file_stash.get(file4_id), None)
		self.assertNotEquals(file_stash.get(file5_id), None)

		# There should be 5 files in the stash both before and after re-indexing
		self.assertEquals(len(file_stash.files), 5)
		file_stash.build_index()
		self.assertEquals(len(file_stash.files), 5)

		# Remove two files with identical content
		file_stash.remove(file3_id)
		self.assertEquals(file_stash.get(file3_id), None)
		self.assertNotEquals(file_stash.get(file5_id), None)
		file_stash.remove(file5_id)
		self.assertEquals(file_stash.get(file3_id), None)
		self.assertEquals(file_stash.get(file5_id), None)

		# Remove one file which has identical name to another file 
		file_stash.remove(file4_id)
		self.assertEquals(file_stash.get(file4_id), None)
#		self.assertNotEquals(file_stash.get(self.file1_name, self.file1_sha1sum), None)

		# At this point, only the first two files should remain in the stash
		file_stash.build_index()
		self.assertEquals(len(file_stash.files), 2)
#		self.assertNotEquals(file_stash.get(self.file1_name, self.file1_sha1sum), None)
#		self.assertNotEquals(file_stash.get(self.file2_name, self.file2_sha1sum), None)

		# Remove all files from stash
		file_stash.nuke()
		self.assertEquals(len(file_stash.files), 0)

	def tearDown(self):
		shutil.rmtree('unittest')

if __name__ == '__main__':
	unittest.main()
