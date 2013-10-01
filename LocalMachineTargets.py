
import json
import os
import unittest

from tasks import CopyFileTask

targets = []

def load(config_filename):
    with open(config_filename) as file:
        global targets
        targets = json.load(file)

def create_distribution_tasks(source_file, source_file_full_path, ids):
    tasks = []
    for id in ids:
        if not id in targets:
            raise Exception("id " + id + " does not exist in targets")
        else:
            target = targets[id]
            destination_file = os.path.join(target['directory'], source_file)
            task = CopyFileTask(source_file_full_path, destination_file)
            tasks.append(task)

    return tasks

def get_targets():
    return targets


class test(unittest.TestCase):
    def setUp(self):
        load('local_machine_targets.json')

    def test(self):
        
        create_distribution_tasks('sourcefile', 'sourcedir/sourcefile', ['target2', 'target3'])

if __name__ == '__main__':
    unittest.main()
