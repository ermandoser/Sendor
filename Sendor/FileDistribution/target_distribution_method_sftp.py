
import os.path

import target_distribution_methods

from actions import SftpSendFileAction

def create_action(task, source, filename, target):	
	return SftpSendFileAction(task, source, filename, target)

target_distribution_methods.register('sftp', create_action)
