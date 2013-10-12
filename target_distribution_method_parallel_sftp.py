
import os.path

import target_distribution_methods

from actions import ParallelSftpSendFileAction

def create_action(task, source, filename, target):	
	return ParallelSftpSendFileAction(task, source, 'test/temp', filename, target)

target_distribution_methods.register('parallel_sftp', create_action)
