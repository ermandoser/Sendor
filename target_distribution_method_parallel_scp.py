
import os.path

import target_distribution_methods

from actions import ParallelScpSendFileAction

def create_action(task, source, filename, target):	
	return ParallelScpSendFileAction(task, source, 'test/temp', filename, target)

target_distribution_methods.register('parallel_scp', create_action)
