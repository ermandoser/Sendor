
import json
import os
import unittest

from SendorQueue import SendorTask

import target_distribution_methods

import target_distribution_method_cp
import target_distribution_method_scp
import target_distribution_method_sftp
import target_distribution_method_parallel_scp
import target_distribution_method_parallel_sftp

class Targets(object):

	def __init__(self, targets):
		self.targets = targets

	def create_distribution_action(self, task, source, filename, id):
		if not id in self.targets:
			raise Exception("id " + id + " does not exist in targets")

		target = self.targets[id]
		action = target_distribution_methods.create_action(task, source, filename, target)

		return action

	def get_targets(self):
		return self.targets


class test(unittest.TestCase):
	def setUp(self):
		with open('test/local_machine_targets.json') as file:
			targets = json.load(file)
			self.targets = Targets(targets)

	def test(self):

		self.targets.create_distribution_action(SendorTask(), 'sourcedir/sourcefile', 'sourcefile', 'target2')

if __name__ == '__main__':
	unittest.main()
